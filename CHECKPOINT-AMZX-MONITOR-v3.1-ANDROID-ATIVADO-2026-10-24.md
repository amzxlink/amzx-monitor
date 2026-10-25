# Checkpoint AMZX Monitor v3.1 — Android ativado

Data: 24/10/2026 (America/Manaus).

## Estado aprovado

PWA independente: https://amzxlink.github.io/amzx-monitor/
Repositório: amzxlink/amzx-monitor, branch main.
Complementa CHECKPOINT-AMZX-MONITOR-v3.1-2026-10-24.md.

Júnior salvou a configuração no Secret AMZX_WEBPUSH_CONFIG. A execução reconheceu 1 aparelho, ativou o teste remoto e terminou com fila de push vazia. Após o teste, o usuário confirmou o recebimento no Android com “Sim”. Som e vibração não foram confirmados separadamente.

## Evidência da validação

Execução: https://github.com/amzxlink/amzx-monitor/actions/runs/40148193053
Commit testado: 29b0cd896073f9cf9c4a066129e828b429539531.
Commit do estado após teste: 003d41c (Atualizar histórico do monitor).
Resultado: sucesso; 54 testes Python e 17 verificações criptográficas aprovados, sintaxe PHP válida.
Amostra histórica: 2026-10-25T00:49:34Z, equivalente a 24/10/2026 às 20:49:34 em Manaus.
Principal, login e Bio responderam HTTP 200 com conteúdo esperado. push_configured=true, 1 aparelho, fila de push vazia. Esta amostra não representa garantia do estado futuro.

## Configuração preservada

- Monitoramento externo pelo GitHub Actions, sem depender da hospedagem AMZX para executar ou enviar alertas.
- Alvos: https://amzx.link/, https://amzx.link/user/login e https://amzx.link/junior.
- Agendamento a cada 5 minutos, sujeito a atrasos ou execuções omitidas pelo GitHub; sem prazo máximo garantido.
- Telegram e Web Push para alertas de queda e recuperação; alertas de lentidão, certificado TLS e resumo diário conforme implementação existente.
- PWA v3.1 responsivo, logo AMZX local, instalação, histórico, CSV e diagnóstico de notificações.
- Secrets mantidos no GitHub; nenhum token, chave privada ou endpoint de inscrição deve ser incluído em arquivos públicos ou no chat.

## Continuidade

Não é necessário cadastrar novamente o Android enquanto a inscrição permanecer válida. Se expirar, preparar novamente as notificações no Android e substituir o Secret com a nova configuração. Não gerar inscrição no navegador remoto para substituir o aparelho do usuário.

Para novo teste remoto, usar Actions → Monitor AMZX → Run workflow com test_push ativado. O workflow também reconhece o commit de teste explicitamente autorizado “Validar ativação e teste remoto do Web Push”. Não disparar simulações sem necessidade.

Não alterar o código de produção do amzx.link ao trabalhar neste monitor. Nenhuma nova alteração de aplicação foi feita para salvar este checkpoint. Novas melhorias devem preservar configurações, histórico e inscrições; não prometer som obrigatório, pois depende do Android e das permissões.
