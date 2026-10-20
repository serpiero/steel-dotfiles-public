import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const folder = new URL('../ui/modules/ii/sidebarLeft/', import.meta.url);
function library(name) {
    const context=vm.createContext({});
    vm.runInContext(readFileSync(new URL(name,folder),'utf8').replace(/^\.pragma library\s*/,''),context);
    return context;
}
const policy=library('WebPanelPolicy.js');
assert.equal(policy.sites(undefined).length,2);
assert.ok(!JSON.stringify(policy.defaults).toLowerCase().includes('audioz'));
assert.deepEqual(Array.from(policy.sites([{name:'Bad',url:'javascript:alert(1)'}]),s=>s.id),['chatgpt','gemini']);
const configured=policy.sites([{id:'personal',name:'Forum',url:'https://example.com',theme:'compact-forum',zoom:2}]);
assert.equal(policy.sites({0:configured[0],length:1})[0].id,"personal","QML list wrappers are accepted");
assert.equal(configured[0].zoom,1.5);
assert.equal(configured[0].theme,'compact-forum');
assert.equal(policy.sites(Array.from({length:10},(_,i)=>({name:String(i),url:'https://example.com'}))).length,6);

const theme=library('WebPanelTheme.js');
const script=theme.script({id:'chatgpt',url:'https://example.com',theme:'compact-forum',background:'#123456',separator:'#abcdef'});
function documentAtCreation(hostname) {
    const nodes=new Map();let change,readyListener,styleCount=0;
    const html={style:{setProperty(){}},classList:{add(){},remove(){}}};
    const appendChild=node=>{styleCount++;nodes.set(node.id,node);};
    const document={documentElement:null,head:null,readyState:'loading',
        getElementById:id=>nodes.get(id),createElement:()=>({}),
        addEventListener:(type,listener)=>{if(type==='DOMContentLoaded')readyListener=listener;}};
    html.appendChild=appendChild;
    const window={};
    const context=vm.createContext({document,window,location:{hostname},URL,requestAnimationFrame:callback=>callback(),console:{info(){}},localStorage:{setItem(){}},
        MutationObserver:class {constructor(callback){change=callback;} observe(){} disconnect(){}}});
    vm.runInContext(script,context);
    assert.equal(nodes.size,0,'DocumentCreation can run before html exists');
    document.documentElement=html;document.head={appendChild};change();readyListener();
    assert.equal(styleCount,1,'Only one stylesheet is installed');
    assert.equal(window.__steelIntelligenceReady,true);
    change();assert.equal(styleCount,1,'SPA additions need no repeated DOM scan');
    return nodes.get('steel-intelligence-theme').textContent;
}
assert.ok(documentAtCreation('example.com').includes('#123456'));
assert.ok(!documentAtCreation('external.example').includes('#123456'),'Forum changes stay in the configured home domain');
console.log('Web panel policy and document-creation theme checks passed.');

// Look-ahead only warms one same-origin HTML document; it creates no second page.
const listeners={}, jobs=[], links=[];
let installedStyle;
const html={style:{setProperty(){}},classList:{add(){},remove(){}}};
const appendChild=node=>{if(node.id)installedStyle=node;else if(node.rel)links.push(node);};
html.appendChild=appendChild;
const doc={documentElement:html,head:{appendChild},readyState:'complete',
    getElementById:()=>installedStyle,createElement:()=>({}),
    addEventListener:(event,callback)=>listeners[event]=callback};
vm.runInContext(theme.script({id:'forum',url:'https://example.com',theme:'compact-forum',background:'#123456',separator:'#abcdef',lookAhead:true}),vm.createContext({
    document:doc,window:{},location:{hostname:'example.com',href:'https://example.com/start.html'},URL,console:{info(){}},
    setTimeout:callback=>{jobs.push(callback);return jobs.length-1;},clearTimeout:id=>{if(id!==undefined)jobs[id]=null;},
    MutationObserver:class {observe(){} disconnect(){}}
}));
function hover(href) { listeners.pointerover({target:{closest:()=>({href})}}); }
hover('https://external.example/file.html');assert.equal(jobs.length,0);
hover('https://example.com/logout.html');assert.equal(jobs.length,0);
hover('https://example.com/download.zip');assert.equal(jobs.length,0);
hover('https://example.com/next.html');assert.equal(jobs.length,1);
jobs[0]();assert.equal(links.length,1);assert.equal(links[0].rel,'prefetch');
hover('https://example.com/other.html');assert.equal(links.length,1);assert.equal(jobs.length,1);
console.log('Bounded HTML-only look-ahead checks passed.');
