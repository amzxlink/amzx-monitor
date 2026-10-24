# AMZX Monitor v3.0

Central de disponibilidade independente do AMZX Link, com PWA para Android, Web Push e Telegram.

## Aplicativo

Após habilitar GitHub Pages, a interface ficará em https://amzxlink.github.io/amzx-monitor/. Em Settings → Pages, escolha Source: GitHub Actions e execute o workflow Publicar AMZX Monitor.

- Painel responsivo com principal, login e Bio.
- Histórico, exportação CSV, cache offline da interface e aviso de dados antigos.
- Push próprio adaptado do AMZX, com chaves e inscrições independentes.
- Alertas de queda, recuperação, lentidão e certificado, com resumo diário após 08h de Manaus.
- Telegram preservado como segundo canal.

## Ativar push no Android

Abra **Avisos**, prepare o aparelho e copie a configuração privada para o Secret **AMZX_WEBPUSH_CONFIG** deste repositório. Execute Monitor AMZX com **Enviar teste de Web Push** marcado. Não publique a configuração nem compartilhe a chave privada. O push e o som precisam ser confirmados no aparelho; não são considerados ativos só por abrir a interface.

O tutorial completo, limites e manutenção estão em [PUSH-E-PWA.md](PUSH-E-PWA.md). O tutorial anterior [ATUALIZAR.md](ATUALIZAR.md) trata da versão 2.0.

## Testes

`python3 -m unittest discover -v`: 54 testes, incluindo os 38 anteriores e as filas independentes de push.

`php verify_push_crypto.php`: 17 verificações com descriptografia pelo receptor, assinatura VAPID e bloqueio de endpoints inválidos. Sem envio externo durante esses testes.

`node --check site/app.js` e `node --check site/sw.js`: sintaxe da interface e worker.

## Operação

Agendamento solicitado a cada cinco minutos, sem garantia de pontualidade do GitHub. Os dados públicos são consultados do repositório; a página sinaliza medições acima de 15 minutos. O envio é executado em Actions, fora da hospedagem AMZX. Não valida transações, banco ou login autenticado. A interface não requer projeto Firebase próprio; o serviço de entrega depende do navegador.
