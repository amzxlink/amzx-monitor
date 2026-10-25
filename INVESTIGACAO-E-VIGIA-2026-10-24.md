# Investigação e reforço do monitor — 24/10/2026

## Escopo e privacidade

Mudanças restritas ao repositório amzxlink/amzx-monitor. Nenhuma mudança no PHP, banco, clientes ou hospedagem de produção. Tokens, inscrições de push e chaves privadas não são arquivos deste pacote: continuam exclusivamente nos Secrets existentes. A nova URL privada do vigia só pode ficar no Secret MONITOR_HEARTBEAT_URL. Nunca enviar seu valor no chat ou adicioná-lo ao config.json.

O repositório é público: horários, disponibilidade, latência, hash identificador do aparelho e histórico já são públicos. Hash não inclui a chave ou o endpoint. Este documento não contém dados de acesso, dumps de banco ou logs internos da hospedagem.

## Implementado

- Registro da conclusão de cada execução e respectivo ID público do GitHub.
- Aviso pelo fluxo atual de Telegram e push quando o monitor retoma após mais de 20 minutos sem conclusão registrada. É uma lacuna de cobertura, não uma declaração de queda do site. Esse aviso só chega após a retomada.
- Integração opcional com vigia externo Healthchecks.io: confirmação apenas depois da persistência do histórico, para o ID da execução atual e conclusão recente. Uma página offline não impede a confirmação de que o monitor executou.
- URL HTTPS privada com UUID, destino restrito a hc-ping.com, sem redirecionamentos. Sem tokens ou respostas remotas nos logs; até três tentativas limitadas.
- Rejeição de páginas HTTP 200 contendo mensagens conhecidas de Composer, SQLSTATE ou erro fatal PHP, mesmo que o nome AMZX apareça.
- Suporte para conferir o destino final exato de um link curto, usando expected_final_url. Sem esse campo, permanece a proteção que rejeita redirecionamento a outro domínio.

## Como ativar o vigia independente

Ainda não está ativo: falta cadastro do serviço e Secret. Não criar URL fictícia.

1. No https://healthchecks.io/, criar um check chamado AMZX Monitor.
2. Em Simple Schedule, configurar Period de 5 minutos e Grace Time de 15 minutos. É uma sugestão operacional: alertará por ausência de confirmação depois de aproximadamente 20 minutos, sujeito ao funcionamento do serviço. Atrasos do GitHub podem gerar alertas legítimos de falta de cobertura.
3. Ativar uma integração de notificação do próprio Healthchecks, como email ou Telegram, associada ao check. O alerta de falta de execução precisa sair dele, pois o GitHub pode estar parado.
4. Copiar a Ping URL no formato HTTPS hc-ping.com/UUID e salvá-la exclusivamente no Secret MONITOR_HEARTBEAT_URL em https://github.com/amzxlink/amzx-monitor/settings/secrets/actions/new.
5. Executar Monitor AMZX e confirmar o log “Vigia externo: conclusão confirmada” e o check atualizado no Healthchecks.
6. Para testar falta de confirmação, usar um check separado de homologação e parar somente seus pings. Não desativar o monitor de produção para simular.

Referências oficiais: https://healthchecks.io/docs/http_api/ ; https://healthchecks.io/docs/configuring_checks/ ; https://healthchecks.io/docs/configuring_notifications/ .

## Redirecionamento de teste

Suporte testado com respostas simuladas; ainda não há alias de teste cadastrado. Criar um link dedicado e estável na conta de homologação, informar seu destino público exato e o texto esperado. Não usar URL com token, login, parâmetros privados, link de cliente ou destino de pagamento. Cadastrar como alvo separado (máximo 10 alvos). Ajustar também TARGETS/NAMES e filtro da interface para exibi-lo no PWA; não declarar cobertura ativa antes disso.

## Situação da investigação

- Principal, login e Bio: acesso público observado. Isso não comprova autenticação, gravação no banco, permissão de cliente ou pagamento.
- Backup/restauração: pendente acesso ao ambiente de homologação e backup de teste. Nunca restaurar sobre produção para testar.
- Banco e tarefas: pendentes dados de execução e acesso controlado à homologação; HTTP 200 não comprova todas as tabelas e crons.
- Pagamentos: pendentes credenciais sandbox e eventos simulados. Não efetuar cobrança ou transferência real.
- Login/permissões: pendentes duas contas de teste e uma conta administrativa de homologação para testar isolamento e privilégios.
- Uploads/Bio: pendente homologação para enviar, trocar, remover e abrir arquivos de teste sem afetar conteúdo real.
- Disco e recursos PHP/cPanel: pendente telemetria da hospedagem; não podem ser medidos pelo acesso público.
- Alerta de vigia independente: código entregue; pendente cadastro/integração/Secret e teste externo real.

## Validação

Antes: 54 testes Python passaram.
Depois: 72 testes Python passaram, incluindo 18 novos cenários de pausa/retomada, URL privada inválida, timeout, execução antiga, redirecionamento correto/incorreto e página de erro com HTTP 200.
PHP não está instalado no ambiente local desta etapa; a sintaxe e os 17 testes criptográficos existentes permanecem no workflow e precisam passar no GitHub após publicação.
Não foram executados testes de pagamento, restauração, isolamento entre contas ou envio de arquivo em produção.
