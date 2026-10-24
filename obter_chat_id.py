"""Executar apenas no computador pessoal. Nunca grava ou imprime o token."""
import getpass
import json
import urllib.request

token = getpass.getpass('Token do BotFather (entrada oculta): ').strip()
try:
    with urllib.request.urlopen('https://api.telegram.org/bot'+token+'/getUpdates', timeout=20) as response:
        payload = json.loads(response.read(1024*1024))
    chats = {}
    for update in payload.get('result', []):
        chat = update.get('message', {}).get('chat', {})
        if 'id' in chat:
            chats[chat['id']] = chat.get('title') or chat.get('first_name') or chat.get('username', 'Chat')
    if not chats:
        print('Nenhum chat encontrado. Abra seu bot, toque Iniciar, envie uma mensagem e tente novamente. Use um bot novo sem webhook.')
    for chat_id, name in chats.items():
        print(f'Chat: {name} | TELEGRAM_CHAT_ID: {chat_id}')
except Exception:
    print('Não foi possível consultar. Confira token, conexão e se este bot usa webhook. Nenhum segredo foi exibido.')
