// Shared rice menu renderer. Keep Electron's command dispatcher and item state;
// only replace the popup surface, whose native Chromium selection ignores CSS.
const {app,BrowserWindow,Menu,screen}=require('electron');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
module.exports=function install(palettePath){
 if(Menu.prototype.__obsidianContextMenu)return;
 const original=Menu.prototype.popup,originalClose=Menu.prototype.closePopup;
 let active;
 const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 Menu.prototype.__obsidianContextMenu=true;
 Menu.prototype.closePopup=function(...args){if(active?.menu===this){active.close();return;}return originalClose.apply(this,args);};
 Menu.prototype.popup=function(options={}){
  const owner=options.window||BrowserWindow.getFocusedWindow();
  if(!owner||owner.isDestroyed()||typeof this._executeCommand!=='function')return original.call(this,options);
  this._callMenuWillShow?.();
  const commands=new Map();let sequence=0,maxRows=0,depth=0;
  const serialize=(menu,level=0)=>{
   depth=Math.max(depth,level);const items=[];
   for(let i=0;i<menu.items.length;i++){
    const item=menu.items[i];if(item.visible===false)continue;
    const id=String(++sequence);commands.set(id,{menu,item});
    let accelerator='';try{accelerator=menu._getAcceleratorTextAt(i)||'';}catch{}
    items.push({id,label:String(item.label||'').replace(/&([^&])/g,'$1').replace(/&&/g,'&'),
     type:item.type,enabled:item.enabled!==false,checked:!!item.checked,
     accelerator,icon:item.icon&&!item.icon.isEmpty?.()?item.icon.toDataURL?.():'',
     children:item.submenu?serialize(item.submenu,level+1):null});
   }
   maxRows=Math.max(maxRows,items.reduce((n,i)=>n+(i.type==='separator'?9:34),8));return items;
  };
  let items;try{items=serialize(this);}catch{return original.call(this,options);}
  if(!items.length)return;
  let colors;try{colors=JSON.parse(fs.readFileSync(palettePath,'utf8'));}catch{return original.call(this,options);}
  active?.close();
  const ownerBounds=owner.getContentBounds(),point=Number.isFinite(options.x)&&Number.isFinite(options.y)?
   {x:ownerBounds.x+options.x,y:ownerBounds.y+options.y}:screen.getCursorScreenPoint();
  const area=screen.getDisplayNearestPoint(point).workArea;
  const longest=Math.max(...[...commands.values()].map(({item})=>String(item.label||'').length));
  const panelWidth=Math.min(340,Math.max(180,100+longest*7));
  const width=Math.min(area.width,panelWidth*(depth+1)),height=Math.min(area.height,maxRows);
  const x=Math.max(area.x,Math.min(point.x,area.x+area.width-width));
  const y=Math.max(area.y,Math.min(point.y,area.y+area.height-height));
  const popup=new BrowserWindow({x,y,width,height,show:false,frame:false,transparent:true,
   backgroundColor:'#00000000',hasShadow:false,resizable:false,minimizable:false,maximizable:false,
   skipTaskbar:true,parent:owner,type:'popup-menu',title:'ObsidianContextMenu',
   webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true,devTools:false}});
  popup.webContents.__obsidianContextMenu=true;
  popup.setMenu(null);const nonce=crypto.randomBytes(12).toString('hex');let closed=false;
  const record={menu:this,close:()=>{
   if(closed)return;closed=true;if(active===record)active=null;
   const restoreFocus=BrowserWindow.getFocusedWindow()===popup;
   if(!popup.isDestroyed())popup.destroy();
   if(restoreFocus&&!owner.isDestroyed())owner.focus();
   owner.removeListener('closed',record.close);watcher?.close();
   if(typeof options.callback==='function')options.callback();
   this.emit('menu-will-close');
  }};active=record;let watcher;
  owner.once('closed',record.close);popup.on('blur',record.close);popup.on('closed',record.close);
  const publishColors=()=>{
   try{const p=JSON.parse(fs.readFileSync(palettePath,'utf8'));popup.webContents.executeJavaScript(
    `for(const [key,value] of Object.entries(${JSON.stringify(p)}))document.documentElement.style.setProperty('--'+key,value)`).catch(()=>{});}catch{}
  };
  try{watcher=fs.watch(path.dirname(palettePath),(_,name)=>{if(!name||name.toString()===path.basename(palettePath))publishColors();});watcher.unref();}catch{}
  popup.webContents.on('will-navigate',e=>e.preventDefault());
  popup.webContents.on('page-title-updated',(e,title)=>{
   e.preventDefault();const prefix='obsidian:'+nonce+':';if(!title.startsWith(prefix))return;
   let event;try{event=JSON.parse(decodeURIComponent(title.slice(prefix.length)));}catch{return;}
   const id=event.id;if(id==='close'){record.close();return;}
   const command=commands.get(id);if(!command||command.item.enabled===false||command.item.submenu)return;
   record.close();if(owner.isDestroyed())return;owner.focus();owner.webContents.focus();
   command.menu._executeCommand({shiftKey:!!event.shiftKey,ctrlKey:!!event.ctrlKey,altKey:!!event.altKey,metaKey:!!event.metaKey},command.item.commandId);
  });
  const css=`:root{${Object.entries(colors).map(([k,v])=>'--'+k+':'+v).join(';')}}
   *{box-sizing:border-box}html,body{margin:0;background:transparent;color:var(--text);font:14px system-ui;user-select:none}
   .menu{position:absolute;top:0;left:0;width:${panelWidth}px;max-height:100vh;overflow-y:auto;background:var(--high);padding:4px;border-radius:8px}
   button{display:flex;align-items:center;gap:8px;width:100%;min-height:34px;padding:6px 10px;margin:0;border:0;border-radius:4px;background:transparent;color:var(--text);font:inherit;text-align:left;outline:none}
   button:disabled{color:var(--muted)}button.active:not(:disabled){background:var(--selection);color:var(--text)}
   .label{flex:1;white-space:nowrap}.accelerator{color:var(--muted);font-size:13px}.mark{width:12px}.icon{width:16px;height:16px}
   hr{border:0;height:1px;background:var(--selection);margin:4px 8px}
   .submenu{display:none}.submenu.open{display:block}`;
  const html=`<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:"><style>${css}</style><body><script>
   const items=${JSON.stringify(items).replace(/</g,'\\u003c')},nonce=${JSON.stringify(nonce)},panelWidth=${panelWidth};
   const send=(id,e={})=>document.title='obsidian:'+nonce+':'+encodeURIComponent(JSON.stringify({id,shiftKey:!!e.shiftKey,ctrlKey:!!e.ctrlKey,altKey:!!e.altKey,metaKey:!!e.metaKey}));let menus=[];
   function hideAfter(level){for(const menu of menus.splice(level+1))menu.remove();}
   function activate(button,level){const menu=menus[level];for(const b of menu.querySelectorAll('button'))b.classList.toggle('active',b===button);hideAfter(level);if(button.childrenItems)build(button.childrenItems,level+1,button.offsetTop);}
   function build(list,level,top=0){hideAfter(level-1);const menu=document.createElement('div');menu.className='menu'+(level?' submenu open':'');menu.style.left=(level*panelWidth)+'px';menu.style.top=Math.min(top,Math.max(0,innerHeight-list.length*34-8))+'px';menu.setAttribute('role','menu');document.body.append(menu);menus[level]=menu;
    for(const item of list){if(item.type==='separator'){menu.append(document.createElement('hr'));continue;}const b=document.createElement('button');b.disabled=!item.enabled;b.dataset.id=item.id;b.childrenItems=item.children;b.setAttribute('role',item.type==='checkbox'?'menuitemcheckbox':item.type==='radio'?'menuitemradio':'menuitem');if(item.type==='checkbox'||item.type==='radio')b.setAttribute('aria-checked',String(item.checked));
     if(item.checked){const mark=document.createElement('span');mark.className='mark';mark.textContent=item.type==='radio'?'●':'✓';b.append(mark);}if(item.icon){const icon=document.createElement('img');icon.className='icon';icon.src=item.icon;b.append(icon);}
     const label=document.createElement('span');label.className='label';label.textContent=item.label;b.append(label);
     const hint=document.createElement('span');hint.className='accelerator';hint.textContent=item.children?'›':item.accelerator;b.append(hint);
     b.onpointerenter=()=>activate(b,level);b.onclick=e=>item.children?activate(b,level):send(item.id,e);menu.append(b);
    }return menu;}
   build(items,0);document.addEventListener('pointerdown',e=>{if(!e.target.closest('.menu'))send('close')});
   document.addEventListener('keydown',e=>{const level=menus.length-1,menu=menus[level],buttons=[...menu.querySelectorAll('button:not(:disabled)')],current=menu.querySelector('button.active'),i=buttons.indexOf(current);let next;
    if(e.key==='Escape'){send('close');return}if(e.key==='ArrowLeft'&&level){hideAfter(level-1);e.preventDefault();return}
    if(e.key==='ArrowDown')next=buttons[(i+1)%buttons.length];if(e.key==='ArrowUp')next=buttons[(i-1+buttons.length)%buttons.length];if(e.key==='Home')next=buttons[0];if(e.key==='End')next=buttons.at(-1);
    if(next){for(const b of buttons)b.classList.toggle('active',b===next);next.scrollIntoView({block:'nearest'});e.preventDefault();return}
    if(current&&['Enter',' ','ArrowRight'].includes(e.key)){if(current.childrenItems){const child=build(current.childrenItems,level+1,current.offsetTop);child.querySelector('button:not(:disabled)')?.classList.add('active')}else if(e.key!=='ArrowRight')send(current.dataset.id,e);e.preventDefault();}
   });</script>`;
  popup.loadURL('data:text/html;charset=utf-8,'+encodeURIComponent(html)).then(()=>{
   if(!closed){popup.show();popup.focus();}
  }).catch(()=>{record.close();if(!owner.isDestroyed())original.call(this,options);});
 };
};
