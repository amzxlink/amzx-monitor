#!/usr/bin/env python3
"""Monitor externo AMZX. Python padrão; nenhum pacote externo."""
import datetime as dt
import json
import os
from pathlib import Path
import socket
import ssl
import math
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo
import time
import urllib.error
import urllib.parse
import urllib.request


def probe(target, opener=urllib.request.urlopen):
    start = time.monotonic()
    try:
        req = urllib.request.Request(target['url'], headers={'User-Agent': 'AMZX-Uptime/1.0', 'Accept-Encoding': 'identity'})
        with opener(req, timeout=20) as response:
            code = response.status
            final = urllib.parse.urlsplit(response.geturl())
            body = response.read(1024 * 1024).decode('utf-8', errors='replace')
        if final.scheme != 'https':
            return False, 'Redirecionamento sem HTTPS', round(time.monotonic()-start, 3)
        if final.hostname != urllib.parse.urlsplit(target['url']).hostname:
            return False, 'Redirecionamento para outro domínio', round(time.monotonic()-start, 3)
        if code != 200:
            return False, f'HTTP {code}', round(time.monotonic()-start, 3)
        if target.get('expected_text', '').casefold() not in body.casefold():
            return False, 'Conteúdo esperado ausente', round(time.monotonic()-start, 3)
        return True, 'HTTP 200 e conteúdo conferido', round(time.monotonic()-start, 3)
    except urllib.error.HTTPError as error:
        code = error.code
        error.close()
        return False, f'HTTP {code}', round(time.monotonic()-start, 3)
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
        # Não imprimir exceções que possam conter credenciais ou conteúdo remoto.
        return False, 'Falha de conexão, DNS, TLS ou tempo limite', round(time.monotonic()-start, 3)


def check(target, probe_fn=probe, pause=time.sleep):
    for attempt in range(3):
        result = probe_fn(target)
        if result[0]:
            return result
        if attempt < 2:
            pause(5)
    return result


def transition(previous, ok, detail, now, name):
    state = dict(previous or {})
    status = 'online' if ok else 'offline'
    old = state.get('status')
    state.setdefault('pending', [])
    if old != status:
        if old is None and ok:
            text = f'✅ Monitor ativado: {name} está online.'
        elif not ok:
            text = f'🔴 {name} está indisponível. Motivo: {detail}. Detectado em {now}.'
            state['down_since'] = now
        else:
            text = f'🟢 {name} voltou a responder. Detectado em {now}. Queda detectada em {state.get("down_since", "horário desconhecido")}.'
            try:
                seconds = max(0, int((dt.datetime.fromisoformat(now)-dt.datetime.fromisoformat(state['down_since'])).total_seconds()))
                text += f' Duração observada: {seconds//60} min {seconds%60} s.'
            except (KeyError, ValueError):
                pass
            state.pop('down_since', None)
        state['pending'].append(text)
    state.update(status=status, checked_at=now, detail=detail)
    return state


def telegram(text, opener=urllib.request.urlopen):
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chat = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
    if not token or not chat:
        print('Telegram: Secret TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID ausente.')
        return False
    try:
        payload = urllib.parse.urlencode({'chat_id': chat, 'text': text, 'disable_web_page_preview': 'true'}).encode()
        req = urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage', data=payload, method='POST')
        with opener(req, timeout=20) as response:
            result = json.loads(response.read(65536))
        if result.get('ok') is True:
            return True
        telegram_error(result.get('error_code'))
    except urllib.error.HTTPError as error:
        telegram_error(error.code)
        error.close()
    except (OSError, ValueError, urllib.error.URLError):
        print('Telegram: falha de rede, TLS ou resposta inválida; envio será tentado novamente.')
    return False


def telegram_error(code):
    reasons = {400: 'Confira o ID do grupo e se ele foi migrado para supergrupo.',
               401: 'Token inválido ou revogado; atualize o Secret.',
               403: 'Bot removido, bloqueado ou sem permissão para enviar.',
               404: 'Confira o token e se foi copiado sem espaços ou horário.',
               429: 'Limite de envios; aguardará a próxima execução.'}
    print(f'Telegram: erro {code if isinstance(code, int) else "não identificado"}. '
          + reasons.get(code, 'Serviço não confirmou o envio; tentará novamente.'))


def flush(state, sender=telegram):
    for _ in range(5):
        if not state['pending']:
            return True
        if not sender(state['pending'][0]):
            return False
        state['pending'].pop(0)
    return not state['pending']


def latency(state, ok, seconds, settings, name):
    threshold = settings.get('slow_seconds', 5)
    required = settings.get('slow_consecutive', 3)
    state['slow_count'] = state.get('slow_count', 0)+1 if ok and seconds >= threshold else 0
    if ok and state['slow_count'] >= required and not state.get('slow_active'):
        state['pending'].append(f'🟠 Lentidão em {name}: {required} verificações consecutivas acima de {threshold}s. Última: {seconds}s.')
        state['slow_active'] = True
    elif ok and seconds < threshold and state.get('slow_active'):
        state['pending'].append(f'🟢 Tempo de resposta normalizado em {name}: {seconds}s.')
        state['slow_active'] = False
    elif not ok:
        state['slow_active'] = False
    return state


def certificate(host):
    context = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=10) as raw:
        with context.wrap_socket(raw, server_hostname=host) as secured:
            return ssl.cert_time_to_seconds(secured.getpeercert()['notAfter'])


def tls_check(meta, hosts, now, threshold=21, fetch=certificate):
    certificates = meta.setdefault('certificates', {})
    today = now.date().isoformat()
    for host in sorted(hosts):
        old = certificates.get(host, {})
        if old.get('checked_date') == today:
            continue
        try:
            expires = fetch(host)
            days = math.floor((expires-now.timestamp())/86400)
            level = 'expired' if days < 0 else 'urgent' if days <= 3 else 'warning' if days <= threshold else 'ok'
            if level != 'ok' and old.get('alert_level') != level:
                meta['pending'].append(f'🔐 HTTPS {host}: certificado expira em aproximadamente {days} dias. Confira a renovação.')
            elif level == 'ok' and old.get('alert_level') in ('warning','urgent','expired','error'):
                meta['pending'].append(f'✅ HTTPS {host}: certificado válido, com aproximadamente {days} dias restantes.')
            certificates[host] = {'checked_date': today, 'alert_level': level, 'days': days,
                                  'expires_at': dt.datetime.fromtimestamp(expires,dt.timezone.utc).isoformat()}
        except (OSError, ValueError, KeyError, ssl.SSLError):
            if old.get('alert_level') != 'error':
                meta['pending'].append(f'⚠️ Não foi possível validar o certificado HTTPS de {host}. Pode ser falha de rede ou TLS; confira o log e o site.')
            certificates[host] = {'checked_date': today, 'alert_level': 'error'}


def daily_summary(meta, history, targets, now, config):
    local = now.astimezone(ZoneInfo(config.get('timezone', 'America/Manaus')))
    # Executa na primeira verificação após 08h; data registrada evita repetição.
    day = (local.date()-dt.timedelta(days=1)).isoformat()
    if local.hour < config.get('summary_hour', 8) or meta.get('summary_day') == day:
        return
    expected = 288
    lines = [f'📊 AMZX — resumo de {day} (Manaus)', 'Disponibilidade entre amostras; não comprova os intervalos sem medição.']
    for target in targets:
        rows = [r for r in history if r['id']==target['id'] and dt.datetime.fromisoformat(r['time']).astimezone(local.tzinfo).date().isoformat()==day]
        slots = {int(dt.datetime.fromisoformat(r['time']).timestamp())//300 for r in rows}
        good = [r for r in rows if r['online']]
        if not rows:
            lines.append(f'{target["name"]}: sem medições nesse dia.')
            continue
        avg = sum(r['seconds'] for r in good)/len(good) if good else 0
        lines.append(f'{target["name"]}: {len(good)/len(rows):.1%} amostras online; {len(rows)-len(good)} falhas/{len(rows)} consultas; tempo médio online {avg:.2f}s; cobertura de janelas de 5 min: {min(100,len(slots)/expected*100):.1f}%.')
    meta['pending'].append('\n'.join(lines))
    meta['summary_day'] = day


def test_report(state, targets, now, config):
    local = now.astimezone(ZoneInfo(config.get('timezone', 'America/Manaus')))
    lines = ['🧪 RESUMO DE TESTE — AMZX',
             local.strftime('%d/%m/%Y às %H:%M (Manaus)'),
             '', 'Estado na verificação atual:']
    for target in targets:
        item = state.get(target['id'], {})
        icon = '🟢' if item.get('status') == 'online' else '🔴'
        lines.append(f'{icon} {target["name"]}: {item.get("status", "desconhecido")} — {item.get("response_seconds", 0):.2f}s')
    for host, cert in state.get('_monitor', {}).get('certificates', {}).items():
        if cert.get('alert_level') == 'error':
            lines.append(f'🔐 HTTPS {host}: consulta de certificado indisponível.')
        else:
            lines.append(f'🔐 HTTPS {host}: aproximadamente {cert.get("days", "?")} dias até vencer.')
    lines += ['', '⏱ Verificação programada: a cada 5 minutos.',
              '📊 Resumo diário: após 08h de Manaus.',
              'Teste pontual. Não indica uma queda e não ativa mensagens a cada consulta.']
    return '\n'.join(lines)


def validate(config):
    targets = config['targets']
    if not 1 <= len(targets) <= 10:
        raise ValueError('Configure entre 1 e 10 alvos.')
    for t in targets:
        url = urllib.parse.urlsplit(t['url'])
        if url.scheme!='https' or not url.hostname or url.port not in (None,443) or url.username or url.password or url.query or url.fragment:
            raise ValueError('Use URL HTTPS pública, porta 443, sem credenciais ou parâmetros.')
        if not isinstance(t.get('expected_text'),str) or not t['expected_text'].strip():
            raise ValueError('Cada alvo precisa de expected_text não vazio.')
    ids=[t['id'] for t in targets]
    if len(set(ids))!=len(ids) or any(i.startswith('_') for i in ids):
        raise ValueError('IDs devem ser únicos e não começar por _.')
    ZoneInfo(config.get('timezone','America/Manaus'))
    return targets


def write_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    temporary.replace(path)


def main():
    config=json.loads(Path('config.json').read_text())
    targets=validate(config)
    path=Path('data/state.json'); hp=Path('data/history.json')
    state=json.loads(path.read_text()) if path.exists() else {}
    history=json.loads(hp.read_text()) if hp.exists() else []
    now=dt.datetime.now(dt.timezone.utc); stamp=now.isoformat(timespec='seconds')
    failed=False
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(check,targets))
    for target,(ok,detail,elapsed) in zip(targets,results):
        item=transition(state.get(target['id']),ok,detail,stamp,target['name'])
        latency(item,ok,elapsed,config,target['name'])
        item['response_seconds']=elapsed
        state[target['id']]=item
        history.append({'time':stamp,'id':target['id'],'online':ok,'seconds':elapsed,'detail':detail})
        failed=failed or not ok
        print(f'{target["id"]}: {"ONLINE" if ok else "OFFLINE"}; {elapsed}s; {detail}')
    meta=state.setdefault('_monitor',{'pending':[]})
    cutoff=now-dt.timedelta(days=32)
    history=[r for r in history if dt.datetime.fromisoformat(r['time'])>=cutoff]
    tls_check(meta,{urllib.parse.urlsplit(t['url']).hostname for t in targets},now,config.get('tls_warning_days',21))
    daily_summary(meta,history,targets,now,config)
    if os.environ.get('SEND_TEST_ALERT')=='true':
        meta['pending'].append(test_report(state, targets, now, config))
    # Persiste antes do envio: preserva medições se o processo for interrompido.
    write_json(hp,history); write_json(path,state)
    for key in [t['id'] for t in targets]+['_monitor']:
        sent=flush(state[key]); failed=failed or not sent
        write_json(path,state)
    if failed:
        print('Execução com site indisponível ou alerta pendente; veja o diagnóstico acima.')
    return int(failed)


if __name__=='__main__':
    raise SystemExit(main())
