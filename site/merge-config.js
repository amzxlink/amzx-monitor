/* Junta configurações somente em memória. Não usa rede, logs ou armazenamento. */
(function(root){
 'use strict';
 const fail=message=>{throw new Error(message);};
 function bytes(value,size){
  if(typeof value!=='string'||!/^[A-Za-z0-9_-]+={0,2}$/.test(value))fail('Uma das chaves do aparelho está inválida. Copie a configuração completa.');
  let out;try{out=Uint8Array.from(atob(value.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));}catch(_){fail('Uma das chaves do aparelho está inválida.');}
  if(out.length!==size)fail('Uma das chaves do aparelho está incompleta.');return out;
 }
 function parse(text,name){
  if(typeof text!=='string'||!text.trim())fail('Cole a configuração '+name+'.');
  if(new TextEncoder().encode(text).length>48000)fail('A configuração é grande demais. Confira o conteúdo copiado.');
  let c;try{c=JSON.parse(text);}catch(_){fail('A configuração '+name+' não é um JSON válido. Copie o código inteiro, sem editar.');}
  if(!c||c.version!==1||!Array.isArray(c.devices)||c.devices.length<1||c.devices.length>5)fail('A configuração '+name+' precisa conter version 1 e uma lista devices com até cinco aparelhos.');
  return c.devices;
 }
 async function validate(d){
  if(!d||typeof d!=='object'||Array.isArray(d))fail('Cadastro de aparelho inválido.');
  let endpoint;try{endpoint=new URL(d.subscription?.endpoint);}catch(_){fail('Inscrição do aparelho incompleta.');}
  const host=endpoint.hostname.toLowerCase();
  if(endpoint.protocol!=='https:'||endpoint.username||endpoint.password||endpoint.hash||endpoint.port||!(['fcm.googleapis.com','updates.push.services.mozilla.com','web.push.apple.com'].includes(host)||host.endsWith('.notify.windows.com')))fail('O endereço de push não é aceito pelo monitor.');
  const pub=bytes(d.public_key,65);if(pub[0]!==4)fail('Chave pública do aparelho inválida.');
  const sub=bytes(d.subscription?.keys?.p256dh,65);if(sub[0]!==4)fail('Chave da inscrição inválida.');bytes(d.subscription?.keys?.auth,16);
  if(typeof d.private_key!=='string'||!/^-----BEGIN PRIVATE KEY-----\s+[A-Za-z0-9+/=\s]+\s+-----END PRIVATE KEY-----\s*$/.test(d.private_key))fail('Chave privada incompleta. Use o código original gerado no aparelho.');
  try{
   const body=d.private_key.replace(/-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\s/g,'');
   const key=await crypto.subtle.importKey('pkcs8',Uint8Array.from(atob(body),c=>c.charCodeAt(0)),{name:'ECDSA',namedCurve:'P-256'},true,['sign']);
   const jwk=await crypto.subtle.exportKey('jwk',key),xy=[...bytes(jwk.x,32),...bytes(jwk.y,32)];
   if(xy.some((v,i)=>v!==pub[i+1]))fail('Chaves pública e privada não correspondem.');
  }catch(_){fail('As chaves do aparelho não correspondem ou estão inválidas. Copie a configuração original completa.');}
  const subject=d.subject||'https://amzxlink.github.io/amzx-monitor/';
  if(typeof subject!=='string'||!/^https:\/\/|^mailto:/.test(subject))fail('Identificação de envio inválida.');
  return {label:typeof d.label==='string'&&d.label.trim()?d.label.trim().slice(0,60):'Android',public_key:d.public_key,private_key:d.private_key,subject,subscription:{endpoint:d.subscription.endpoint,keys:{p256dh:d.subscription.keys.p256dh,auth:d.subscription.keys.auth}}};
 }
 async function merge(previous,next){
  const entries=[...parse(previous,'anterior'),...parse(next,'do novo aparelho')],devices=[];
  for(const input of entries){
   const d=await validate(input),existing=devices.find(v=>v.subscription.endpoint===d.subscription.endpoint);
   if(existing){
    if(existing.public_key!==d.public_key||existing.private_key.replace(/\s/g,'')!==d.private_key.replace(/\s/g,'')||existing.subscription.keys.p256dh!==d.subscription.keys.p256dh||existing.subscription.keys.auth!==d.subscription.keys.auth)fail('O mesmo aparelho apareceu com chaves diferentes. Confira os cadastros; nenhuma configuração foi substituída.');
    continue;
   }
   devices.push(d);
  }
  if(devices.length>5)fail('O monitor aceita no máximo cinco aparelhos. Nenhum cadastro foi removido.');
  return {version:1,devices};
 }
 root.AMZXMerge={merge};
 if(typeof module!=='undefined'&&module.exports)module.exports=root.AMZXMerge;
})(typeof globalThis!=='undefined'?globalThis:this);
