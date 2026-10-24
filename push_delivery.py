"""Push independente do Telegram; inscrições/chaves somente no Secret do runner."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def devices():
    raw=os.environ.get('AMZX_WEBPUSH_CONFIG','').strip()
    if not raw:
        return None
    config=json.loads(raw)
    items=config['devices']
    if not isinstance(items,list) or not 1<=len(items)<=5:
        raise ValueError('invalid device list')
    return [hashlib.sha256(d['subscription']['endpoint'].encode()).hexdigest() for d in items]


def queue_events(state, target_ids, ids):
    meta=state['_monitor']
    queue=meta.setdefault('push_queue',[])
    seen=meta.setdefault('push_seen',[])
    if not ids:
        meta['push_configured']=False
        return
    meta['push_configured']=True
    for key in target_ids+['_monitor']:
        for text in state[key].get('pending',[]):
            fingerprint=hashlib.sha256((key+'\n'+text).encode()).hexdigest()
            if fingerprint in seen:
                continue
            seen.append(fingerprint)
            urgent=text.startswith(('🔴','🟠','⚠️','🔐'))
            queue.append({'id':fingerprint,'remaining':list(ids),'payload':{
                'title':'AMZX Monitor · '+('Alerta' if urgent else 'Atualização'),
                'body':text[:600], 'tag':'amzx-'+fingerprint[:24], 'url':'./',
                'urgent':urgent,'renotify':True}})
    meta['push_seen']=seen[-2000:]


def send_packet(packet):
    try:
        result=subprocess.run(['php',str(Path(__file__).with_name('push_sender.php'))],input=json.dumps(packet),text=True,capture_output=True,timeout=85,check=False)
        data=json.loads(result.stdout)
        return data.get('results',[])
    except (OSError,ValueError,subprocess.TimeoutExpired):
        return []


def deliver(state, ids, sender=send_packet):
    meta=state['_monitor']; queue=meta.setdefault('push_queue',[])
    if not ids:
        return True
    active=set(ids); success=True
    for event in queue[:5]:
        event['remaining']=[i for i in event['remaining'] if i in active]
        results=sender(event) if event['remaining'] else []
        for result in results:
            identity=result.get('id');status=result.get('status')
            if identity not in event['remaining']:continue
            if status=='sent':event['remaining'].remove(identity)
            elif status=='expired':
                event['remaining'].remove(identity)
                print('Web Push: inscrição expirada; reative o aparelho e atualize o Secret.')
                meta['push_needs_renewal']=True
            else:
                print('Web Push: envio pendente; diagnóstico '+str(status if status in ('authorization','configuration','retry') else 'retry'))
        if event['remaining']:success=False
    meta['push_queue']=[e for e in queue if e['remaining']]
    return success and not meta['push_queue']
