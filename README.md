# Monitor externo AMZX v2.0

Monitor gratuito para GitHub Actions com Telegram. Independente da hospedagem AMZX, sem alterar o encurtador.

## Recursos

- Agendamento a cada 5 minutos (melhor esforço do GitHub).
- Landing page, login e Bio com HTTP 200, HTTPS/domínio final e trecho esperado no HTML.
- Três tentativas antes de registrar queda.
- Avisos de queda e recuperação, com duração observada e fila persistente.
- Lentidão acima de 5 segundos em três verificações online consecutivas; aviso de normalização.
- Verificação diária do certificado TLS, aviso antecipado e de renovação.
- Resumo do dia anterior na primeira execução após 08h de Manaus, com cobertura de medições e disponibilidade entre amostras.
- Botão manual para enviar mensagem de teste, sem alterar o site.
- Diagnóstico do Telegram por código, sem expor token ou corpo remoto.
- Histórico recente de 32 dias, com estado compatível com v1.

**Atualização e testes no GitHub:** veja [ATUALIZAR.md](ATUALIZAR.md). Preserve os Secrets e a pasta data existentes.

Para instalação nova, envie os arquivos à raiz do repositório público, incluindo .github/workflows/monitor.yml. Cadastre os Secrets TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID em Settings → Secrets and variables → Actions. O bot deve pertencer ao grupo e poder enviar mensagens. Não envie o token para o código. Permita contents: write para salvar estado/histórico. Execute Actions → Monitor AMZX → Run workflow com a opção de teste marcada. O script cria data automaticamente na primeira execução.

Teste local sem envio real: `python3 -m unittest discover -v`. Python 3.10 ou posterior, biblioteca padrão, nenhum pacote pip. Testado com 38 casos: migração v1, quedas, recuperação, fila, lentidão, resumo e fuso, cobertura, certificados e diagnóstico sem vazamento.

Não é verificação de login autenticado, pagamentos ou banco. Não garante monitoramento em tempo real. Leia as limitações no tutorial. Não publique URLs privadas, tokens ou informações pessoais; os resultados ficam no repositório público. Nenhuma página de status ou web push foi adicionada.

## Fontes oficiais

- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://docs.github.com/en/actions/concepts/billing-and-usage
- https://core.telegram.org/bots/api
- https://github.com/actions/checkout
