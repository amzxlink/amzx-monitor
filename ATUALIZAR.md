# Atualizar o repositório amzxlink/amzx-monitor para v2.0

Não muda o AMZX nem exige novo bot. Preserve os Secrets e os arquivos data/state.json e data/history.json existentes. A atualização lê o estado v1, mantendo avisos pendentes e o histórico; novos alvos recebem sua primeira mensagem de ativação.

## Etapa 1 — guardar uma cópia

Abra https://github.com/amzxlink/amzx-monitor, selecione Code → Download ZIP para guardar o estado anterior. Esse ZIP não contém Secrets.

## Etapa 2 — pausar enquanto troca os arquivos

Em Actions → Monitor AMZX, menu de três pontos → Disable workflow. Se houver execução em andamento, aguarde terminar antes de editar. Isso evita execução com metade dos arquivos antigos e metade novos.

## Etapa 3 — substituir os arquivos da raiz

Extraia o pacote v2.0. No repositório, Code → Add file → Upload files.

Envie estes arquivos extraídos, diretamente para a raiz:

- monitor.py
- config.json
- test_monitor.py
- test_improvements.py (novo)
- README.md
- ATUALIZAR.md

Clique Commit changes e confirme na branch principal main. Não envie o ZIP, não crie uma pasta envolvendo os arquivos e não apague ou substitua a pasta data. obter_chat_id.py continua opcional e não precisa ser alterado.

A configuração pronta verifica:

1. https://amzx.link/ — palavra AMZX no HTML.
2. https://amzx.link/user/login — palavra password no HTML.
3. https://amzx.link/junior — nome Francisco Junior no HTML.

Esses endereços foram conferidos por consulta pública, mas as respostas HTTP do runner e a presença dos marcadores precisam ser confirmadas na primeira execução. Se a Bio ou nome mudar, ajuste expected_text. Não use palavras que mudam a cada visita.

## Etapa 4 — substituir o workflow

Na aba Code, entre em .github → workflows → monitor.yml e clique no lápis (Edit this file).

Abra no computador o NOVO arquivo .github/workflows/monitor.yml com o Bloco de Notas, copie todo o conteúdo e substitua todo o conteúdo no editor do GitHub. Salve com Commit changes na main.

A pasta .github pode estar oculta no computador. Ative a exibição de itens ocultos. Não crie outro workflow com nome diferente: substitua o existente, para não executar dois monitores.

Os campos ${{ secrets.TELEGRAM_BOT_TOKEN }} e ${{ secrets.TELEGRAM_CHAT_ID }} ficam como estão, sem colar token no código. Os Secrets já cadastrados continuam funcionando.

## Etapa 5 — reativar e testar

Em Actions → Monitor AMZX → Enable workflow (ou menu de três pontos → Enable workflow).

Clique Run workflow, selecione main, marque Enviar mensagem de teste ao Telegram e confirme Run workflow. Deixe essa opção desmarcada nas execuções normais; o agendamento nunca a marca sozinho.

Confirme:

- 38 testes aprovados na etapa Testar o monitor.
- AMZX principal, login e Bio online na etapa de verificação (ou um motivo específico caso algum falhe).
- Mensagem de teste no grupo. Login e Bio podem enviar ativação por serem novos alvos.
- Etapa Salvar estado e histórico concluída e data/state.json atualizado.
- Na segunda execução normal, nenhuma ativação ou teste repetido.

Se falhar: abra check → etapa vermelha. O Telegram agora mostra diagnóstico por código 400/401/403/404/429, sem imprimir token ou corpo remoto. 400 pode indicar grupo/ID incorreto; 401 token inválido; 403 permissão/bloqueio; 429 limite de envios. A causa exata pode exigir conferir a configuração.

## Testar queda e recuperação sem tirar o AMZX do ar

No config.json, altere SOMENTE expected_text do alvo amzx para TESTE_INDISPONIBILIDADE_9b4d7c. Salve, execute manualmente e confira o aviso de queda. Repita sem alteração: não deve duplicar a queda. Volte expected_text para AMZX, salve e execute: deve chegar recuperação com duração observada. A simulação testa conteúdo, não falha real de DNS/servidor.

## Ajustes disponíveis

- Intervalo: 5 minutos no cron novo. Execuções do GitHub podem atrasar ou ser descartadas.
- Lentidão: slow_seconds=5 e slow_consecutive=3. Avisa após três verificações online consecutivas lentas, não três tentativas na mesma execução. Avisa quando normalizar.
- Certificado: tls_warning_days=21. Verifica uma vez por dia UTC; avisa aos 21 dias, ao entrar em até 3 dias, se expirado e quando renovar. Se falhar a consulta, tenta no dia seguinte; a checagem HTTP de cada execução também valida TLS.
- Resumo diário: summary_hour=8 e timezone=America/Manaus. Na primeira execução após 08h, resume o dia anterior; não é uma execução com horário garantido. Na primeira ativação pode informar ausência de dados do dia anterior.
- Até dez alvos HTTPS em config.json, com IDs únicos. Os três prontos são suficientes para começar. Não use parâmetros, senhas, tokens ou URLs privadas.

## Voltar à versão anterior

Pause o workflow. Restaure monitor.py, config.json, test_monitor.py e .github/workflows/monitor.yml da cópia antiga; apague test_improvements.py, pois os testes dele exigem v2. Mantenha data intacta. Reative e execute manualmente. A chave _monitor é ignorada pela versão v1; a fila de resumo/certificado só volta a ser processada pela v2.

## Limitações

O monitor observa uma única origem externa, sem executar JavaScript nem fazer login/pagamento. Não demonstra que banco, cron ou todas as funções AMZX estão saudáveis. Não mede desempenho visual, Core Web Vitals ou experiência do visitante. O tempo registrado é da tentativa HTTP bem-sucedida ou da última falha, sem somar as esperas de repetição.

A disponibilidade do resumo é a proporção de amostras online. A cobertura conta janelas distintas de cinco minutos, evidenciando intervalos sem consulta; não representa um SLA de disponibilidade por tempo. A duração de queda é entre detecção e detecção de recuperação, não o instante exato em que o servidor caiu/voltou.

GitHub pode atrasar/descartar agendamentos e desativá-los após 60 dias sem atividade. Verifique a aba Actions periodicamente. O monitor não tem vigilância independente de suas próprias execuções. As medições fazem commits reais e o histórico Git cresce. A retenção no arquivo é 32 dias; commits anteriores permanecem. Repositório público expõe status/nomes/URLs/horários; Secrets continuam fora dos arquivos.

Mensagens são reenviadas se houver falha de entrega. Podem duplicar em interrupção entre envio e persistência/push. São enviados no máximo cinco alertas pendentes por alvo por execução, para limitar rajadas. A fila continua nas próximas execuções. Horários dos eventos técnicos são UTC; o resumo diário usa Manaus.

Nada foi aplicado ao seu repositório por este pacote. Os testes automatizados são simulados; o envio real ao seu grupo e a execução do novo workflow precisam ser confirmados na etapa 5. Sem web push ou página pública de status nesta versão.
