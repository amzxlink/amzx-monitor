#!/usr/bin/env python3
"""Monitor externo AMZX. Python padrão; nenhum pacote externo."""
import datetime as dt
import json
import os
from pathlib import Path
import socket
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
        return False, f'HTTP {error.code}', round(time.monotonic()-start, 3)
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
            state.pop('down_since', None)
        state['pending'].append(text)
    state.update(status=status, checked_at=now, detail=detail)
    return state


def telegram(text, opener=urllib.request.urlopen):
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chat = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
    if not token or not chat:
        return False
    try:
        payload = urllib.parse.urlencode({'chat_id': chat, 'text': text, 'disable_web_page_preview': 'true'}).encode()
        req = urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage', data=payload, method='POST')
        with opener(req, timeout=20) as response:
            return json.loads(response.read(65536)).get('ok') is True
    except (OSError, ValueError, urllib.error.URLError):
        return False


def flush(state, sender=telegram):
    while state['pending']:
        if not sender(state['pending'][0]):
            return False
        state['pending'].pop(0)
    return True


def main():
    targets = json.loads(Path('config.json').read_text())['targets']
    for target in targets:
        url = urllib.parse.urlsplit(target['url'])
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('Use somente URL HTTPS pública sem credenciais, parâmetros ou fragmentos.')
    ids = [t['id'] for t in targets]
    if len(set(ids)) != len(ids) or not targets:
        raise ValueError('Configure ao menos um alvo, com IDs únicos.')
    path = Path('data/state.json')
    state = json.loads(path.read_text()) if path.exists() else {}
    history_path = Path('data/history.json')
    history = json.loads(history_path.read_text()) if history_path.exists() else []
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    failed = False
    for target in targets:
        ok, detail, elapsed = check(target)
        item = transition(state.get(target['id']), ok, detail, now, target['name'])
        item['response_seconds'] = elapsed
        sent = flush(item)
        failed = failed or not ok or not sent
        state[target['id']] = item
        history.append({'time': now, 'id': target['id'], 'online': ok, 'seconds': elapsed, 'detail': detail})
        print(f'{target["id"]}: {"ONLINE" if ok else "OFFLINE"}; {elapsed}s; alertas pendentes: {len(item["pending"])}')
    Path('data').mkdir(exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n')
    history_path.write_text(json.dumps(history[-1000:], ensure_ascii=False, indent=2)+'\n')
    if failed:
        print('Site indisponível ou alerta pendente. Consulte o estado e os Secrets.')
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
