"""Liveness checks. Public state never contains heartbeat URLs or credentials."""
import datetime as dt
import json
import os
from pathlib import Path
import re
import urllib.request


def recovery(meta, now, previous_checks=(), threshold_minutes=20):
    previous = meta.get('completed_at')
    if not previous:
        candidates = [v for v in previous_checks if v]
        previous = min(candidates) if candidates else None
    if not previous:
        return
    try:
        gap = (now - dt.datetime.fromisoformat(previous)).total_seconds()
    except (ValueError, TypeError):
        return
    if gap > threshold_minutes * 60:
        meta.setdefault('pending', []).append(
            f'⚠️ Monitor retomado após {int(gap // 60)} minutos sem conclusão registrada. '
            'Esse intervalo ficou sem cobertura confirmada; não significa queda do site.')
        meta['last_gap'] = {'resumed_at': now.isoformat(timespec='seconds'), 'seconds': int(gap)}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def heartbeat(state, environ=None, opener=None, now=None):
    env = os.environ if environ is None else environ
    url = env.get('MONITOR_HEARTBEAT_URL', '').strip()
    if not url:
        print('Vigia externo: não configurado; cadastre MONITOR_HEARTBEAT_URL.')
        return True
    # Restrict secret destination, disallow redirects and never print remote errors.
    if not re.fullmatch(r'https://hc-ping\.com/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', url):
        print('Vigia externo: configuração inválida; use a URL HTTPS UUID do Healthchecks.')
        return False
    meta = state.get('_monitor', {})
    try:
        age = ((now or dt.datetime.now(dt.timezone.utc)) - dt.datetime.fromisoformat(meta['completed_at'])).total_seconds()
        valid = bool(env.get('GITHUB_RUN_ID')) and meta.get('completed_run_id') == env['GITHUB_RUN_ID'] and 0 <= age <= 600
    except (KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        print('Vigia externo: execução atual não concluiu; confirmação não enviada.')
        return False
    send = opener or urllib.request.build_opener(NoRedirect()).open
    for _ in range(3):
        try:
            request = urllib.request.Request(url, data=b'', method='POST', headers={'User-Agent': 'AMZX-Monitor-Heartbeat/1.0'})
            with send(request, timeout=10) as response:
                if response.status == 200:
                    print('Vigia externo: conclusão confirmada.')
                    return True
        except (OSError, ValueError):
            pass
    print('Vigia externo: não confirmou recebimento; confira a execução e o serviço.')
    return False


if __name__ == '__main__':
    try:
        state = json.loads(Path('data/state.json').read_text())
        result = heartbeat(state)
    except (OSError, ValueError):
        print('Vigia externo: estado indisponível; confirmação não enviada.')
        result = False
    raise SystemExit(0 if result else 1)
