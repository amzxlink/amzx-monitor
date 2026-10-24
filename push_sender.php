<?php
/** Web Push extraído e adaptado de Helpers\Amzx\WebPush (AMZX Link).
 * Sem banco, framework ou estado da hospedagem AMZX. Entrada/saída JSON via stdin/stdout.
 * Nunca imprime endpoints, chaves privadas, Authorization ou respostas remotas.
 */
declare(strict_types=1);
final class MonitorPush {
    public static function b64(string $v): string {return rtrim(strtr(base64_encode($v), '+/', '-_'), '=');}
    public static function decode(string $v): string {
        $r=base64_decode(strtr($v,'-_','+/'),true);
        if($r===false)throw new RuntimeException('base64');return $r;
    }
    public static function publicPem(string $point): string {
        if(strlen($point)!==65||$point[0]!=="\x04")throw new RuntimeException('point');
        return "-----BEGIN PUBLIC KEY-----\n".chunk_split(base64_encode(hex2bin('3059301306072a8648ce3d020106082a8648ce3d030107034200').$point),64,"\n")."-----END PUBLIC KEY-----\n";
    }
    public static function expand(string $prk,string $info,int $length): string {
        $out='';$t='';for($i=1;strlen($out)<$length;$i++){$t=hash_hmac('sha256',$t.$info.chr($i),$prk,true);$out.=$t;}return substr($out,0,$length);
    }
    public static function rawSignature(string $der): string {
        $offset=0;
        $read=function()use(&$offset,$der):int{$n=ord($der[$offset++]);if(!($n&128))return $n;$c=$n&127;$n=0;for($i=0;$i<$c;$i++)$n=($n<<8)|ord($der[$offset++]);return $n;};
        if(ord($der[$offset++])!==48)throw new RuntimeException('DER');$read();
        if(ord($der[$offset++])!==2)throw new RuntimeException('DER');$n=$read();$r=substr($der,$offset,$n);$offset+=$n;
        if(ord($der[$offset++])!==2)throw new RuntimeException('DER');$n=$read();$s=substr($der,$offset,$n);
        return str_pad(ltrim($r,"\0"),32,"\0",STR_PAD_LEFT).str_pad(ltrim($s,"\0"),32,"\0",STR_PAD_LEFT);
    }
    public static function endpoint(string $endpoint): string {
        $p=parse_url($endpoint);$h=strtolower((string)($p['host']??''));
        // Limita envios aos provedores Web Push suportados; impede URL arbitrária/SSRF.
        $allowed=in_array($h,['fcm.googleapis.com','updates.push.services.mozilla.com','web.push.apple.com'],true)||str_ends_with($h,'.notify.windows.com');
        if(!$allowed||($p['scheme']??'')!=='https'||($p['port']??443)!==443||isset($p['user'])||isset($p['pass'])||isset($p['fragment']))throw new RuntimeException('endpoint');
        return 'https://'.$h;
    }
    public static function packet(array $sub,array $payload,array $config): array {
        $aud=self::endpoint((string)($sub['endpoint']??''));
        $public=self::decode((string)($sub['keys']['p256dh']??''));$auth=self::decode((string)($sub['keys']['auth']??''));
        if(strlen($auth)!==16)throw new RuntimeException('auth');
        $peer=openssl_pkey_get_public(self::publicPem($public));
        $key=openssl_pkey_get_private((string)($config['private_key']??''));
        $details=$key?openssl_pkey_get_details($key):false;
        if(!$details||($details['ec']['curve_name']??'')!=='prime256v1')throw new RuntimeException('vapid');
        $vapid="\x04".$details['ec']['x'].$details['ec']['y'];
        if(!hash_equals(self::b64($vapid),(string)($config['public_key']??'')))throw new RuntimeException('vapid mismatch');
        $subject=(string)($config['subject']??'https://amzxlink.github.io/amzx-monitor/');
        if(!preg_match('#^(mailto:|https://)#',$subject))throw new RuntimeException('subject');
        $ephemeral=openssl_pkey_new(['private_key_type'=>OPENSSL_KEYTYPE_EC,'curve_name'=>'prime256v1']);
        $d=openssl_pkey_get_details($ephemeral);$local="\x04".$d['ec']['x'].$d['ec']['y'];
        $shared=openssl_pkey_derive($peer,$ephemeral,32);if($shared===false)throw new RuntimeException('ECDH');
        $prk=hash_hmac('sha256',$shared,$auth,true);
        $ikm=self::expand($prk,"WebPush: info\0".$public.$local,32);$salt=random_bytes(16);
        $prk=hash_hmac('sha256',$ikm,$salt,true);$cek=self::expand($prk,"Content-Encoding: aes128gcm\0",16);$nonce=self::expand($prk,"Content-Encoding: nonce\0",12);
        $json=json_encode($payload,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR);
        if(strlen($json)>3000)throw new RuntimeException('payload too long');
        $cipher=openssl_encrypt($json."\x02",'aes-128-gcm',$cek,OPENSSL_RAW_DATA,$nonce,$tag,'',16);
        if($cipher===false)throw new RuntimeException('encrypt');
        $body=$salt.pack('N',4096).chr(strlen($local)).$local.$cipher.$tag;
        $input=self::b64('{"typ":"JWT","alg":"ES256"}').'.'.self::b64(json_encode(['aud'=>$aud,'exp'=>time()+3600,'sub'=>$subject],JSON_UNESCAPED_SLASHES));
        if(!openssl_sign($input,$der,$key,OPENSSL_ALGO_SHA256))throw new RuntimeException('sign');
        $jwt=$input.'.'.self::b64(self::rawSignature($der));
        return ['body'=>$body,'headers'=>['Content-Type: application/octet-stream','Content-Encoding: aes128gcm','TTL: 300','Urgency: '.(!empty($payload['urgent'])?'high':'normal'),'Authorization: vapid t='.$jwt.', k='.self::b64($vapid),'Content-Length: '.strlen($body)]];
    }
    public static function send(array $sub,array $payload,array $config): string {
        $packet=self::packet($sub,$payload,$config);
        $options=['http'=>['method'=>'POST','header'=>implode("\r\n",$packet['headers']),'content'=>$packet['body'],'timeout'=>15,'ignore_errors'=>true,'follow_location'=>0], 'ssl'=>['verify_peer'=>true,'verify_peer_name'=>true]];
        @file_get_contents($sub['endpoint'],false,stream_context_create($options));
        $status=preg_match('/\s(\d{3})\s/',$http_response_header[0]??'',$m)?(int)$m[1]:0;
        if($status>=200&&$status<300)return 'sent';
        if(in_array($status,[404,410],true))return 'expired';
        if(in_array($status,[401,403],true))return 'authorization';
        return 'retry';
    }
}
if(realpath($_SERVER['SCRIPT_FILENAME']??'')===__FILE__){
    ini_set('display_errors','0');error_reporting(0);
    try{
        $config=json_decode((string)getenv('AMZX_WEBPUSH_CONFIG'),true,64,JSON_THROW_ON_ERROR);
        $input=json_decode(stream_get_contents(STDIN),true,64,JSON_THROW_ON_ERROR);
        $results=[];$wanted=$input['remaining']??[];
        foreach(array_slice($config['devices']??[],0,5) as $device){
            $sub=$device['subscription']??[];$id=hash('sha256',(string)($sub['endpoint']??''));if(!in_array($id,$wanted,true))continue;
            try{$status=MonitorPush::send($sub,$input['payload'],$device);}catch(Throwable $e){$status='configuration';}
            $results[]=['id'=>$id,'status'=>$status];
        }
        echo json_encode(['results'=>$results],JSON_THROW_ON_ERROR);
    }catch(Throwable $e){echo '{"error":"configuration","results":[]}';exit(1);}
}
