# Checkpoint — AMZX Monitor v3.1
Data: 24/10/2026 · Manaus, Amazonas

## Identidade e ponto de restauração
- Proprietário: Júnior.
- Repositório: https://github.com/amzxlink/amzx-monitor
- Aplicativo publicado: https://amzxlink.github.io/amzx-monitor/
- Commit de referência antes deste checkpoint: `1a7800fbdf8baba803478cc8dda1b7b8f529ee7d`.
- Não confundir este projeto independente com o código PHP do AMZX Link.
- Preservar o estado em data/, os Secrets existentes, a origem do PWA, o escopo do Service Worker e as chaves VAPID de aparelhos em uso.

## O que já foi entregue
- Monitor de principal, login e Bio /junior, com conteúdo esperado além do HTTP 200.
- Agendamento solicitado a cada 5 minutos; 3 tentativas antes de declarar falha.
- Telegram com queda, recuperação, lentidão persistente, certificado HTTPS e resumo diário após 08h de Manaus.
- Fila de alertas, histórico e registro de execuções.
- PWA no GitHub Pages, independente da hospedagem AMZX.
- Painel responsivo, histórico, exportação CSV, diagnóstico e indicação de dados antigos.
- Web Push adaptado do AMZX Link: VAPID ES256, ECDH P-256 e aes128gcm.
- Envio de push separado do Telegram, com fila por aparelho e prioridade alta para alertas.
- Logotipo oficial obtido do ícone do próprio AMZX e copiado para os arquivos do monitor, sem dependência de download do AMZX durante o uso.
- Visual v3.1 refinado; botão de instalação visível mesmo sem convite automático.
- Instruções de instalação manual, ícones 192/512, máscara Android e cache atualizado.

## Evidência verificada
- 54 testes Python do monitor e filas passaram na etapa v3.0.
- 17 verificações criptográficas PHP passaram, incluindo descriptografia pelo receptor e assinatura VAPID.
- 8 verificações do Service Worker passaram.
- 16 verificações do fluxo de instalação passaram na etapa v3.1.
- Revisão de navegação e layout em larguras de 320 e 390 pixels, sem transbordamento horizontal.
- Publicação v3.1 concluída: https://github.com/amzxlink/amzx-monitor/actions/runs/40141629897
- Manifesto, worker, logotipo e ícones públicos retornaram HTTP 200 e hashes iguais aos arquivos testados.
- Telegram já recebeu mensagens reais e testes de resumo/queda. O usuário informou que o som do Telegram não tocou.
- Não afirmar que a instalação no Android ou o som do push foram comprovados: dependem do aparelho do proprietário.

## Estado observado ao salvar
- Última medição registrada: 2026-10-24T22:44:51+00:00 (18h44min51s de Manaus).
- Nessa medição: principal, login e Bio online; filas do Telegram vazias.
- Isso é um registro histórico, não uma confirmação da situação atual do site.
- Última execução programada listada: https://github.com/amzxlink/amzx-monitor/actions/runs/40139860442 — sucesso.
- Web Push na última medição: `push_configured: false`; nenhum aparelho reconhecido.
- A presença atual dos Secrets não foi consultada. Se o usuário já os cadastrou depois, executar o workflow antes de concluir que faltam.

## Próxima etapa — ativar no Android
1. Abrir o aplicativo no Chrome atualizado: https://amzxlink.github.io/amzx-monitor/
2. Tocar em Instalar app; confirmar no navegador ou seguir Adicionar à tela inicial.
3. Abrir Avisos → Preparar notificações e permitir notificações.
4. Copiar a configuração privada para um Secret de repositório chamado AMZX_WEBPUSH_CONFIG.
5. Não publicar esse JSON em arquivo nem enviá-lo no chat: contém a chave privada e a inscrição do aparelho.
6. Executar Actions → Monitor AMZX → Run workflow, marcando Enviar teste de Web Push para os aparelhos cadastrados.
7. Confirmar entrega com app fechado e tela bloqueada, som e vibração.
8. Confirmar que o painel reconhece o aparelho depois da atualização de estado.

## Depois da ativação
- Testar queda e recuperação simuladas sem interromper o AMZX, verificando Telegram e push.
- Conferir que não há spam quando o estado permanece igual.
- Examinar regularidade das execuções schedule. Foram observados dados antigos durante a revisão, e o painel os sinaliza.
- Se precisar de detecção em prazo previsível, adicionar monitor independente: GitHub não garante pontualidade e pode descartar agendamentos.
- Considerar vigiar também a parada do próprio monitor. Ainda não existe um vigia independente do GitHub.

## Limites e cuidados
- Web Push não obriga o Android a tocar. O som depende do navegador/PWA, permissões, volume e Não Perturbe.
- Teste de áudio com a tela aberta não comprova toque em segundo plano.
- Configuração inicial exporta um aparelho. Para vários, preservar todos os objetos devices no mesmo Secret (limite 5).
- Alterar chaves exige reinscrição e atualização do Secret.
- A conexão GitHub utilizada permite editar código e acompanhar workflows, mas não expõe cadastro de Secrets ou administração de Pages.
- Nunca pedir token, chave privada ou senha pelo chat.
- As checagens públicas não validam banco, pagamentos ou login autenticado.
- Nenhuma alteração desta etapa foi aplicada ao encurtador/AMZX Link.
- Documentação: PUSH-E-PWA.md; o tutorial ATUALIZAR.md refere-se à versão anterior 2.0.

## Contexto do projeto principal
A auditoria e correções PHP do AMZX Link foram entregues anteriormente como v1.5.861-RC1 para homologação. Testes locais não substituem os testes em clone na hospedagem com MySQL/MariaDB real, instalador completo e restauração. Não marcar esse pacote como homologado em produção por causa do trabalho no monitor.

## Instrução de retomada
Continuar a partir deste checkpoint, verificar o estado atual do repositório e da última execução e priorizar a ativação/teste real no Android. Não recriar o projeto nem sobrescrever Secrets, inscrições ou histórico.
