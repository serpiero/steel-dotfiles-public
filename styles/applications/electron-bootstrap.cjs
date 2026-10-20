const {app}=require('electron');
const fs=require('node:fs');
const path=require('node:path');
HOST_SETUP
if ((process.env.XDG_CURRENT_DESKTOP||'').toLowerCase().includes('hyprland')) {
  require(CONTEXT_MENU_MODULE)(NATIVE_PALETTE_PATH);
  const records=new Map();
  const cssPath=CSS_PATH;
  async function update(contents,record) {
    if (contents.__obsidianContextMenu) return;
    if (record.busy) {record.again=true;return;}
    record.busy=true;
    try {
      const css=fs.readFileSync(cssPath,'utf8');
      // Insert first: a palette update must never expose the original surfaces.
      const key=await contents.insertCSS(css,{cssOrigin:'user'});
      const old=record.key;record.key=key;
      if (old) await contents.removeInsertedCSS(old).catch(()=>{});
      if (process.env.OBSIDIAN_STYLE_TEST_OUTPUT) {
        const result=await contents.executeJavaScript('({body:getComputedStyle(document.body).backgroundColor,root:getComputedStyle(document.documentElement).backgroundColor})');
        fs.writeFileSync(process.env.OBSIDIAN_STYLE_TEST_OUTPUT,JSON.stringify(result));
      }
    } catch(error) {if(!contents.isDestroyed()) console.warn('[Obsidian palette]',error.message);}
    finally {record.busy=false;if(record.again){record.again=false;update(contents,record);}}
  }
  app.on('web-contents-created',(_,contents)=> {
    const record={key:null,busy:false,again:false};records.set(contents,record);
    contents.on('did-finish-load',()=>update(contents,record));
    contents.once('destroyed',()=>records.delete(contents));
  });
  // Watch the parent: the generator replaces CSS atomically, changing its inode.
  let timer;
  const watcher=fs.watch(path.dirname(cssPath),(_,filename)=> {
    if(filename && filename.toString()!==path.basename(cssPath)) return;
    clearTimeout(timer);
    timer=setTimeout(()=>records.forEach((record,contents)=>update(contents,record)),60);
  });
  watcher.unref();
  app.once('will-quit',()=>{clearTimeout(timer);watcher.close();});
}
require(ORIGINAL_MAIN);
