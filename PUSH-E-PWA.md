# AMZX Monitor v3.0 — PWA independente

PWA de disponibilidade instalado pelo Chrome no Android. Envio Web Push adaptado de WebPush.php/Pwa.php do AMZX Link, com VAPID ES256, ECDH P-256 e aes128gcm. O código não usa o servidor AMZX para cadastrar aparelhos ou entregar alertas. O monitor continua no GitHub Actions e o Telegram permanece ativo.

## Publicar a interface (uma vez)

1. No repositório, abra **Settings → Pages**.
2. Em **Build and deployment → Source**, escolha **GitHub Actions**.
3. Abra **Actions → Publicar AMZX Monitor → Run workflow**.
4. Espere a publicação verde. Endereço esperado: `https://amzxlink.github.io/amzx-monitor/`.

A conexão de edição usada neste projeto não expõe administração de Pages ou cadastro de Secrets. Por isso, esses passos de conta devem ser feitos pelo proprietário. Nenhuma chave privada foi adicionada ao repositório.

## Instalar e ativar no Android

1. Abra o endereço publicado no Chrome atualizado, fora do modo anônimo.
2. Use **Instalar aplicativo** ou o menu do Chrome → **Adicionar à tela inicial / Instalar aplicativo**.
3. Abra **Avisos → Preparar notificações** e permita as notificações.
4. Toque **Copiar configuração privada**. Mantenha a tela aberta até copiar; a chave privada não é persistida no navegador.
5. No link **Abrir novo Secret**, use o nome exato **AMZX_WEBPUSH_CONFIG** e cole a configuração no campo Secret. Se já existir, edite esse Secret. Não crie um arquivo público com esse conteúdo e não o compartilhe no chat.
6. Em **Actions → Monitor AMZX → Run workflow**, marque **Enviar teste de Web Push para os aparelhos cadastrados** e execute.
7. Confira a notificação no Android e o log Web Push do workflow. O painel identifica seu aparelho quando a próxima consulta do estado contiver o hash da inscrição.
8. Teste com a tela bloqueada. Confira volume, notificações com som para o Chrome/PWA e Não Perturbe no Android. O som não pode ser imposto por Web Push; o botão de áudio desta tela não altera o toque em segundo plano.

A primeira configuração contém **um aparelho**. Substituir o Secret por uma nova configuração troca o aparelho anterior. Para até cinco aparelhos, mantenha no mesmo JSON a lista `devices` de cada configuração, preservando as chaves correspondentes. O navegador não recebe chave de GitHub, token de Telegram ou Secrets anteriores.

## Como funciona sem servidor de cadastro

A página gera um par VAPID local usando WebCrypto e cria uma inscrição no navegador. Ela entrega ao proprietário um JSON privado para cadastrar como Secret. Nenhum endpoint público recebe essa chave e nenhuma senha/token GitHub é solicitado pelo aplicativo. O Actions recebe o Secret somente no runner e usa o emissor PHP para enviar ao serviço push do navegador. No Chrome/Android, o transporte normalmente usa a infraestrutura push do Google, sem exigir um projeto Firebase seu.

Trocar chaves requer nova inscrição. Depois de recarregar a tela, se precisar copiar novamente, refaça a preparação e atualize o Secret; o app avisa antes de revogar a inscrição anterior. Não basta copiar só o endpoint: as chaves precisam corresponder.

## Privacidade e controles

- A publicação contém só arquivos estáticos da pasta `site/`. O emissor PHP, testes e arquivos de estado do repositório não fazem parte do pacote Pages.
- O painel consulta apenas estado e histórico públicos do monitor. Tokens e inscrições não ficam nesses arquivos; somente hashes dos aparelhos e estado de entrega.
- Web Push é independente do Telegram, com fila e controle de entrega por aparelho. Falha de um canal não bloqueia a tentativa do outro.
- Envios usam TLS validado, não seguem redirecionamentos e aceitam somente provedores push conhecidos (Google, Mozilla, Apple e Windows).
- Registros não incluem chaves, endpoints, cabeçalhos de autorização ou respostas remotas.
- Mensagens expiradas (404/410) pedem renovação do aparelho. TTL de 5 minutos impede que o provedor guarde um alerta urgente por muito tempo; a fila local pode tentar novamente no próximo workflow.
- O cache offline contém apenas a interface. Medições são carregadas pela rede e o estado antigo fica identificado. A cópia local de estado/histórico é pública, sem Secrets.
- O histórico de versões e o estado anteriores são preservados no Git.

## O que é medido

Principal, login e Bio com HTTP 200 e conteúdo esperado. Percentual de amostras online nas últimas 24 horas; tempo de obtenção do HTML, não Lighthouse. Barras representam consultas, sem preencher lacunas. Estado acima de 15 minutos é sinalizado como antigo. Hora da interface em Manaus; logs técnicos UTC. Agendamento GitHub é melhor esforço, sem garantia de intervalo exato. O PWA não transforma agendamentos atrasados em monitoramento instantâneo.

## Verificação

- 54 testes Python: 38 anteriores e 16 de fila/entrega Web Push, sem mensagens reais.
- 17 verificações criptográficas PHP: descriptografia pelo lado receptor, Unicode, JWT, assinatura ES256 verificada, urgência, TTL, chaves incompatíveis e endpoints maliciosos.
- 8 verificações automatizadas do Service Worker, incluindo vibração, sinalização de alerta, clique seguro e preservação do cache de outros apps.
- JavaScript validado com node --check; navegação/histórico/permissão negada e ausência de transbordamento horizontal conferidos no navegador, incluindo iframe de largura mobile.
- Entrega real ao Android e som só podem ser confirmados após permitir notificações e cadastrar o Secret no aparelho do proprietário.

## Manutenção

Para alterar as páginas ou o intervalo, edite `config.json` e o workflow do monitor, como antes. Os três serviços do painel v3 têm nomes/endereço definidos no `site/app.js`; se adicionar outros alvos, atualize também essa lista. Publicações da interface não apagam a inscrição, desde que origem, escopo do worker e chaves sejam preservados. Não remova a chave privada do Secret enquanto houver aparelhos em uso.
