const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const src=fs.readFileSync('site/app.js','utf8');
const block=src.slice(src.indexOf('// O atalho de instalação'),src.indexOf('async function worker()'));
function setup(ua='Android Chrome',standalone=false){const nodes={},events={},hooks={};function node(id){return nodes[id]??=( {hidden:false,textContent:'',open:false,addEventListener:(name,fn)=>hooks[id+':'+name]=fn,showModal(){this.open=true},close(){this.open=false}});}
 const ctx={navigator:{userAgent:ua},matchMedia:()=>({matches:standalone}),window:{addEventListener:(key,fn)=>events[key]=fn},document:{querySelectorAll:()=>[{addEventListener:(key,fn)=>hooks['banner:'+key]=fn}]},$:node,toast:()=>{},worker:async()=>({update:async()=>{}}),installPrompt:null};vm.createContext(ctx);vm.runInContext(block,ctx);return {ctx,nodes,events,hooks};}
(async()=>{let checks=0,s=setup();assert.equal(s.nodes.install.hidden,false);checks++;assert.equal(s.nodes['install-banner'].hidden,false);checks++;assert.equal(s.nodes['install-native'].hidden,true);checks++;s.hooks['install:click']();assert.equal(s.nodes['install-dialog'].open,true);checks++;assert.match(s.nodes['install-guidance'].textContent,/Chrome do Android/);checks++;s.hooks['close-install:click']();assert.equal(s.nodes['install-dialog'].open,false);checks++;
let prompted=0,prevented=0;s.events.beforeinstallprompt({preventDefault:()=>prevented++,prompt:async()=>prompted++,userChoice:Promise.resolve({outcome:'accepted'})});assert.equal(prevented,1);checks++;assert.equal(s.nodes['install-native'].hidden,false);checks++;await s.hooks['install-native:click']();assert.equal(prompted,1);checks++;assert.equal(s.nodes['install-dialog'].open,false);checks++;
s.events.appinstalled();assert.equal(s.nodes.install.hidden,true);checks++;assert.equal(s.nodes['install-banner'].hidden,true);checks++;
s=setup('Android',true);assert.equal(s.nodes.install.hidden,true);checks++;assert.equal(s.nodes['install-banner'].hidden,true);checks++;
s=setup('iPhone Safari');assert.match(s.nodes['install-guidance'].textContent,/Safari/);checks++;
s=setup('Windows Chrome');assert.match(s.nodes['install-guidance'].textContent,/Chrome ou Edge/);checks++;
console.log(checks+' verificações da instalação PWA passaram.');})().catch(e=>{console.error(e.message);process.exit(1)});
