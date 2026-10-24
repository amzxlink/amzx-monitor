# AMZX — Monitor externo básico v1.0

Verifica https://amzx.link/ aproximadamente a cada 10 minutos, independentemente da hospedagem AMZX. Não instala nem altera nada no encurtador. Faz GET da página, valida HTTPS/domínio final, HTTP 200 e a palavra AMZX no primeiro MiB de HTML. Não valida login, banco, pagamentos ou toda a aplicação. Uma página quebrada contendo AMZX pode passar: adapte `expected_text` a um trecho estável e exclusivo, se necessário.

## 1. Preparar o Telegram

1. No Telegram, abra o bot oficial **@BotFather**, envie `/newbot` e siga os passos para criar um bot exclusivo deste monitor.
2. Copie o token. Não coloque esse token em arquivos do repositório, prints ou mensagens públicas.
3. Abra o seu novo bot, toque **Iniciar/Start** e envie `teste`.
4. Para descobrir o ID da conversa, instale Python 3 no seu computador, abra um terminal nesta pasta e execute `python obter_chat_id.py` (no Windows, pode ser `py obter_chat_id.py`). Cole o token quando solicitado: a entrada fica oculta e o token não é salvo. O resultado mostra seu `TELEGRAM_CHAT_ID`.
5. Guarde token e ID para cadastrar nos Secrets abaixo. O auxiliar usa getUpdates; crie um bot novo sem webhook. Se não encontrar conversa, envie outra mensagem ao bot e repita.

## 2. Criar o repositório

1. Entre em https://github.com/new.
2. Nome: `amzx-monitor`. Selecione **Public** para usar executores padrão gratuitos. Este repositório contém só o monitor, nunca os arquivos/configuração do AMZX.
3. Marque **Add a README file** e crie o repositório.
4. Extraia o ZIP no computador. Entre na pasta que contém `monitor.py` e `config.json`.
5. No GitHub, escolha **Add file → Upload files**. Arraste os arquivos e as pastas desta pasta, incluindo **`.github` e `data`**, para a área de upload. Não envie o ZIP nem coloque tudo dentro de uma pasta extra.
6. Clique em **Commit changes** na branch principal (`main`).
7. Confira que existe o caminho **`.github/workflows/monitor.yml`** no repositório e que `monitor.py` e `config.json` estão na raiz. Alguns sistemas ocultam a pasta `.github`: ative a visualização de itens ocultos. Se ela não subir, use **Add file → Create new file**, nome `.github/workflows/monitor.yml`, e copie o conteúdo do arquivo local correspondente.

Estrutura esperada:
- `.github/workflows/monitor.yml`
- `monitor.py`
- `config.json`
- `test_monitor.py`
- `data/.gitkeep`
- demais arquivos de documentação/auxiliar.

## 3. Cadastrar os Secrets

No repositório: **Settings → Secrets and variables → Actions → New repository secret**.

Crie estes dois Secrets com os nomes exatos:

| Nome | Valor |
| --- | --- |
| TELEGRAM_BOT_TOKEN | Token recebido do BotFather |
| TELEGRAM_CHAT_ID | ID obtido no passo 1 |

Não são Variables; use **Secrets**. Nada precisa ser colocado no código. Se o token vazar, revogue-o no BotFather e substitua o Secret.

## 4. Permitir salvar o histórico

Em **Settings → Actions → General**, permita o uso de Actions. Em **Workflow permissions**, selecione **Read and write permissions**, se disponível, e salve. O workflow já solicita apenas `contents: write`; políticas da organização ou proteção da branch podem impedir o push. Não é preciso habilitar criação/aprovação de pull requests nem criar um token pessoal.

Se a branch bloquear commits do bot, use um repositório dedicado sem essa proteção. O estado precisa ser salvo para evitar alertas repetidos.

## 5. Executar e confirmar

1. Abra **Actions → Monitor AMZX → Run workflow → Run workflow** na branch principal.
2. Aguarde a execução. Na primeira verificação online, o Telegram deve receber **“Monitor ativado: AMZX Link está online”**.
3. Confirme que surgiram `data/state.json` e `data/history.json` no repositório e que a etapa de salvar histórico passou.
4. Execute novamente: se continuar online, não deve repetir a mensagem de ativação.
5. Depois de cadastrar tudo, as próximas verificações ocorrem automaticamente nos minutos 07, 17, 27, 37, 47 e 57 de cada hora. O agendamento é UTC, mas o intervalo é o mesmo no Brasil.

Sem Secrets válidos, a execução fica vermelha e mantém o alerta pendente. Site offline também deixa a execução vermelha: veja o log para distinguir queda de erro de configuração. O histórico pode ser atualizado mesmo com execução vermelha.

## 6. Testar queda e recuperação sem derrubar o AMZX

1. Primeiro confirme a mensagem de ativação online.
2. Em `config.json`, altere só `expected_text` de `AMZX` para `TESTE_INDISPONIBILIDADE_9b4d7c` e salve/commit.
3. Execute o workflow manualmente. O site real continua normal, mas a validação falha três vezes: deve chegar o aviso vermelho de indisponibilidade.
4. Execute novamente sem mudar nada: não deve repetir o mesmo aviso.
5. Volte `expected_text` para `AMZX`, salve e execute. Deve chegar o aviso verde de recuperação.
6. Confirme que o estado voltou a `online` e a lista `pending` ficou vazia.

Esse teste comprova validação, persistência e entrega pelo seu Telegram. Os testes automáticos incluídos usam respostas simuladas e não enviam mensagens reais.

## 7. Trocar para 15 minutos

Em `.github/workflows/monitor.yml`, substitua a linha cron por:

```yaml
    - cron: '7,22,37,52 * * * *'
```

Salve na branch principal. Não é necessário manter computador ligado nem contratar hospedagem.

## Histórico e comportamento

- Três tentativas por verificação, com cinco segundos entre falhas; até 20 segundos de timeout por requisição. É a visão de uma única origem (runner do GitHub), não consenso de vários locais.
- O alerta sai quando uma execução detecta falha: não é instantâneo e depende também da disponibilidade do GitHub/Telegram.
- Registra estado e últimas 1.000 medições, com horários em UTC e tempo até ler o HTML; isso não é tempo de renderização do navegador.
- Envia ativação, queda e recuperação, sem notificações periódicas de sucesso.
- Entrega falhou? Mantém a fila para tentar na próxima execução; pode enviar eventos anteriores quando o Telegram voltar. Em falha entre envio e commit, pode haver duplicação: não há garantia de entrega exatamente uma vez.
- Cada execução grava medições reais por commit. O histórico do Git cresce; mesmo com limite de 1.000 no arquivo, commits antigos permanecem.
- Repositório público expõe URL, status e histórico. Não coloque URLs com tokens, dados pessoais ou endpoints privados na configuração. O auxiliar de chat não salva o token.
- GitHub pode atrasar ou descartar agendamentos; em repositórios públicos, workflows agendados podem ser desativados após 60 dias sem atividade. Verifique a aba Actions periodicamente e reative se necessário. Este monitor não garante SLA nem monitora a própria falha de agendamento.
- Cloudflare pode bloquear o runner: 403/429 ou desafio podem gerar alerta mesmo com acesso normal por navegador. Investigue sem desativar a segurança geral do site.
- Sem web push nesta versão; alertas via Telegram.

## Testes executados antes da entrega

18 testes automatizados passaram: HTTP 200 correto, falso HTTP 200, erro 520, timeout, domínio diferente, redirecionamento HTTP, três tentativas, recuperação na segunda tentativa, ativação, primeira queda, ausência de spam, recuperação, fila pendente, limpeza da fila, Secrets ausentes, Telegram aceito/rejeitado e serialização do estado. Comando: `python3 -m unittest -v test_monitor.py`.

Nenhum bot real foi usado, nenhum workflow foi executado na sua conta e nenhum serviço foi instalado em produção. Faça a confirmação real dos passos 5 e 6.

## Referências oficiais

- GitHub: agendamento e limitações: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- Gratuidade: https://docs.github.com/en/actions/concepts/billing-and-usage
- Secrets: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
- Telegram Bot API: https://core.telegram.org/bots/api
- BotFather e criação: https://core.telegram.org/bots/tutorial
