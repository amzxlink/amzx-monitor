<?php
require __DIR__.'/push_sender.php';
$count=0;
function check($ok,$label){global $count;if(!$ok)throw new RuntimeException('Falhou: '.$label);$count++;}
function keypair(){ $k=openssl_pkey_new(['private_key_type'=>OPENSSL_KEYTYPE_EC,'curve_name'=>'prime256v1']);openssl_pkey_export($k,$pem);$d=openssl_pkey_get_details($k);return [$k,$pem,"\x04".$d['ec']['x'].$d['ec']['y']]; }
[$browser,$bp,$bpublic]=keypair();[$vapid,$vp,$vpublic]=keypair();$auth=random_bytes(16);
$sub=['endpoint'=>'https://fcm.googleapis.com/fcm/send/synthetic','keys'=>['p256dh'=>MonitorPush::b64($bpublic),'auth'=>MonitorPush::b64($auth)]];
$config=['public_key'=>MonitorPush::b64($vpublic),'private_key'=>$vp];$payload=['title'=>'Teste AMZX','body'=>'Não houve queda real.','urgent'=>true];
$packet=MonitorPush::packet($sub,$payload,$config);$body=$packet['body'];$salt=substr($body,0,16);$record=unpack('N',substr($body,16,4))[1];$size=ord($body[20]);$ephemeral=substr($body,21,$size);$cipher=substr($body,21+$size);$shared=openssl_pkey_derive(openssl_pkey_get_public(MonitorPush::publicPem($ephemeral)),$browser,32);
// Lado receptor independente: hash_hkdf nativo, sem usar expand() do emissor.
$ikm=hash_hkdf('sha256',$shared,32,"WebPush: info\0".$bpublic.$ephemeral,$auth);
$cek=hash_hkdf('sha256',$ikm,16,"Content-Encoding: aes128gcm\0",$salt);$nonce=hash_hkdf('sha256',$ikm,12,"Content-Encoding: nonce\0",$salt);
$plaintext=openssl_decrypt(substr($cipher,0,-16),'aes-128-gcm',$cek,OPENSSL_RAW_DATA,$nonce,substr($cipher,-16),'');
check($record===4096,'record size');check($size===65,'public point size');check(substr($plaintext,-1)==="\x02",'padding delimiter');check(json_decode(substr($plaintext,0,-1),true)===$payload,'decrypt and unicode');check(in_array('Urgency: high',$packet['headers'],true),'high urgency');check(in_array('TTL: 300',$packet['headers'],true),'TTL');
$header=implode("\n",$packet['headers']);preg_match('/vapid t=([^,]+),/',$header,$matches);$parts=explode('.',$matches[1]);$claims=json_decode(MonitorPush::decode($parts[1]),true);check($claims['aud']==='https://fcm.googleapis.com','audience');check($claims['exp']>time()&&$claims['exp']<=time()+3600,'expiry');
$raw=MonitorPush::decode($parts[2]);check(strlen($raw)===64,'JOSE signature size');
$encode=function($v){$v=ltrim($v,"\0");if(ord($v[0])&128)$v="\0".$v;return "\x02".chr(strlen($v)).$v;};$ints=$encode(substr($raw,0,32)).$encode(substr($raw,32));$der="\x30".chr(strlen($ints)).$ints;
check(openssl_verify($parts[0].'.'.$parts[1],$der,openssl_pkey_get_public(MonitorPush::publicPem($vpublic)),OPENSSL_ALGO_SHA256)===1,'signature verified');
foreach(['https://127.0.0.1/x','http://fcm.googleapis.com/x','https://fcm.googleapis.com.evil.example/x','https://user:pass@fcm.googleapis.com/x','https://fcm.googleapis.com:444/x']as $url){$blocked=false;try{MonitorPush::endpoint($url);}catch(RuntimeException $e){$blocked=true;}check($blocked,'blocked endpoint');}
$blocked=false;try{MonitorPush::packet($sub,['body'=>str_repeat('x',3500)],$config);}catch(RuntimeException $e){$blocked=true;}check($blocked,'payload bound');
$blocked=false;try{MonitorPush::packet($sub,$payload,['public_key'=>'wrong','private_key'=>$vp]);}catch(RuntimeException $e){$blocked=true;}check($blocked,'mismatched key');
echo "$count verificações criptográficas passaram, sem envio externo.\n";
