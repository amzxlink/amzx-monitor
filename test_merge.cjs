const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {webcrypto}=require('node:crypto');if(!globalThis.crypto)globalThis.crypto=webcrypto;
const {merge}=require('./site/merge-config.js');
let checks=0;const pass=(condition)=>{assert.ok(condition);checks++;};
const b64=x=>Buffer.from(x).toString('base64url');
async function device(i){const keys=await crypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},true,['sign','verify']);return {label:'Android '+i,public_key:b64(await crypto.subtle.exportKey('raw',keys.publicKey)),private_key:'-----BEGIN PRIVATE KEY-----\n'+Buffer.from(await crypto.subtle.exportKey('pkcs8',keys.privateKey)).toString('base64')+'\n-----END PRIVATE KEY-----\n',subject:'https://amzxlink.github.io/amzx-monitor/',subscription:{endpoint:'https://fcm.googleapis.com/fcm/send/fixture-'+i,keys:{p256dh:b64(await crypto.subtle.exportKey('raw',keys.publicKey)),auth:b64(new Uint8Array(16).fill(i))}}};}
const config=devices=>JSON.stringify({version:1,devices});
async function reject(fn,pattern){await assert.rejects(fn,pattern);checks++;}
(async()=>{
 const all=await Promise.all([1,2,3,4,5,6].map(device)),a=config([all[0]]),b=config([all[1]]);
 const combined=await merge(a,b);pass(combined.devices.length===2);pass(combined.devices[0].private_key===all[0].private_key);pass(combined.devices[1].subscription.endpoint===all[1].subscription.endpoint);
 pass((await merge(a,a)).devices.length===1);
 pass((await merge(config(all.slice(0,4)),config([all[4]]))).devices.length===5);
 await reject(()=>merge(config(all.slice(0,5)),config([all[5]])),/máximo cinco/);
 await reject(()=>merge('{',b),/JSON válido/);await reject(()=>merge('',b),/Cole/);await reject(()=>merge(JSON.stringify({version:2,devices:all}),b),/version 1/);
 const bad=structuredClone(all[1]);bad.private_key=all[0].private_key;await reject(()=>merge(a,config([bad])),/chaves/);
 const evil=structuredClone(all[1]);evil.subscription.endpoint='https://evil.example/';await reject(()=>merge(a,config([evil])),/endereço de push/);
 const missing=structuredClone(all[1]);delete missing.subscription.keys.auth;await reject(()=>merge(a,config([missing])),/chaves/);
 const clash=structuredClone(all[0]);clash.subscription.keys.auth=all[1].subscription.keys.auth;await reject(()=>merge(a,config([clash])),/mesmo aparelho/);
 const label=structuredClone(all[1]);label.label='<img onerror=alert(1)>';pass((await merge(a,config([label]))).devices[1].label===label.label);
 await reject(()=>merge('x'.repeat(48001),b),/grande demais/);
 // UI controls use synthetic configurations only. Ensure copy/invalidation/clear semantics.
 const src=fs.readFileSync('site/app.js','utf8'),block=src.slice(src.indexOf('// Vários aparelhos:'));
 const nodes={},hooks={},events={},clipboard=[];const $=id=>nodes[id]??={value:'',disabled:false,hidden:true,textContent:'',addEventListener:(event,fn)=>hooks[id+':'+event]=fn};
 const ctx={$: $,AMZXMerge:{merge},privateConfig:b,window:{addEventListener:(e,fn)=>events[e]=fn},navigator:{clipboard:{writeText:async text=>clipboard.push(text)}},toast:()=>{}};
 vm.createContext(ctx);vm.runInContext(block,ctx);$('merge-previous').value=a;$('merge-next').value=b;await hooks['merge-build:click']();pass($('merge-copy').disabled===false&&JSON.parse($('merge-result').value).devices.length===2);
 await hooks['merge-copy:click']();pass(JSON.parse(clipboard[0]).devices.length===2);
 hooks['merge-next:input']();pass($('merge-copy').disabled&&$('merge-result').value==='');
 $('merge-previous').value=a;$('merge-next').value=b;await hooks['merge-build:click']();events.pagehide();pass($('merge-previous').value===''&&$('merge-next').value===''&&$('merge-result').value===''&&$('merge-copy').disabled);
 const html=fs.readFileSync('site/index.html','utf8');pass(html.indexOf('src="merge-config.js"')<html.indexOf('src="app.js"'));
 const core=fs.readFileSync('site/merge-config.js','utf8');pass(!/\bfetch\s*\(|localStorage|console\./.test(core));
 console.log(checks+' verificações da junção privada de aparelhos passaram.');
})().catch(()=>{console.error('Teste de junção falhou. Conteúdo privado omitido.');process.exitCode=1;});
