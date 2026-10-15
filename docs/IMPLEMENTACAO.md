# Implementação e limites

## Entrega por fases

1. Auditoria pública de uma página via Celery, relatório privado por sessão/conta, pontuação documentada, sitemap por lista e robots com prévia/download. Páginas indexáveis de SEO, sitemap, robots, IndexNow, consulta A/AAAA e CIDR.
2. Conta, limite de domínios, propriedade por chave HTTPS, envio IndexNow em lote, histórico e intervalo entre reenvios. A chave é revalidada no worker antes de qualquer envio. Não há rastreamento profundo.
3. OAuth Google com state de uso único, expiração e PKCE; tokens cifrados Fernet; consulta agregada de cliques, impressões, CTR e posição em 28 dias (com defasagem de 3 dias), inspeção da raiz e envio de sitemap; monitoramento periódico com alertas no painel.
4. Testes automatizados, imagens de execução, exemplos Nginx e restrições de saída. **Implantação real, firewall e integração com contas reais ainda precisam de configuração e validação no servidor de destino.**

O portal estático, o QR Code e suas bibliotecas são preservados. Nenhum banco, .env ou Nginx existente foi modificado. Os acréscimos ao HTML original são links para SEO e Global Ping. A ferramenta Global Ping está detalhada em GLOBALPING.md.

## Pontuação

A soma fixa é 100: HTTP 2xx (20), título de 30 a 60 caracteres (10), descrição de 70 a 160 (10), um H1 com hierarquia H1–H3 sem saltos (10), ausência de noindex/none em robots e X-Robots-Tag (10), imagens com atributo alt (5), presença de canonical (5), sitemap XML padrão disponível (5), robots padrão disponível (5), indício de Schema.org (5), HTTPS final (5), Open Graph básico e Twitter Card (5), viewport device-width (5).

Faixas de tamanho são referências editoriais internas. Os testes de presença não comprovam validade semântica de canonical ou Schema.org. Alt vazio é aceito para imagens decorativas. A pontuação não é oficial do Google, não prevê ranking nem garante indexação. Links, tempo HTTP e PageSpeed não entram na nota. A ordem dos problemas é crítico, atenção, recomendação.

## Rede e privacidade

`core/network.py` aceita apenas HTTP/HTTPS nas portas 80/443, rejeita credenciais e caracteres de controle, valida todos os IPs DNS em cada salto e conecta ao IP aprovado sem nova resolução. HTTPS mantém SNI e verifica certificado. O socket valida o par conectado. Existem limite de resposta, leitura em blocos, limite de saltos e timeout; respostas comprimidas são recusadas. O timeout total não interrompe uma chamada do resolvedor do sistema: configure timeout DNS no host e mantenha o limite rígido Celery.

A análise pública consulta uma página, robots, sitemap e no máximo MAX_LINK_CHECKS links internos por HEAD, sem recursão. O host bloqueado no admin é recusado pelo cliente. O limitador Redis é atômico e aplica limites por IP e usuário; cabeçalhos X-Forwarded-For recebidos não são confiados. Atrás de Nginx, configure TRUSTED_PROXY_IPS com o IP exato do proxy e faça o Nginx sobrescrever X-Real-IP, evitando que todos os usuários compartilhem um só limite. Não inclua clientes nessa lista. Configure também proteção de volume no proxy.

Relatórios exigem a sessão criadora ou a conta proprietária, inclusive quando seu UUID é conhecido. Rotas privadas e respostas POST recebem noindex e no-store. Sitemap público contém somente páginas públicas. Tokens OAuth são cifrados, excluídos do admin e nunca incluídos em relatórios. Configure remoção periódica de auditorias/atividades e backups cifrados conforme sua política de retenção. Logs de requisições não devem registrar query strings de OAuth nem corpos de formulários.

Workers devem rodar isolados, sem privilégios e com bloqueio de rede para destinos internos. Compose oferece isolamento de processo/recursos, **mas não instala firewall de saída**. O exemplo nftables é uma referência nativa; adapte e teste a política de rede para containers antes de abrir a auditoria ao público. O cliente Python protege as conexões de usuários; o firewall é a segunda camada obrigatória. DB, Redis e DNS precisam de exceções estritas; nunca libere uma sub-rede inteira só para permitir um serviço.

## Operação e serviços externos

- Search Console: configure OAuth no Google Cloud, habilite Search Console API e registre exatamente `SITE_URL/integracoes/google/callback/`. A aplicação exige propriedade exata `sc-domain:host` ou `https://host/` com permissão `siteOwner`, além da chave local. Não utiliza Google Indexing API. Não percorre propriedades filhas nem oferece inspeção arbitrária; consulta a raiz verificada. A API de inspeção descreve a versão conhecida pelo índice, não um teste ao vivo.
- PageSpeed: opcional via PAGESPEED_API_KEY. Quando houver quota e dados, mostra performance de laboratório e métricas de campo retornadas. Sem dados, informa indisponibilidade; viewport não comprova compatibilidade móvel.
- IndexNow: 200 significa recebido; 202 indica validação pendente. Não faz retry automático. Reenvie pela interface após o intervalo para manter controle de frequência. Chave HTTPS na raiz sem redirecionamentos é uma exigência adicional desta aplicação.
- Google/Bing do próprio portal: o sitemap e robots ficam disponíveis, mas adicionar a propriedade no Google/Bing e publicar as provas de propriedade depende das contas do administrador. Nenhuma conta foi conectada automaticamente.
- Monitoramento: um Beat por instalação; intervalo configurável. Verifica disponibilidade, TLS/expiração, título, descrição, diretivas, sitemap e sinais de rastreamento. Alertas são exibidos no painel; não envia e-mail/SMS. O botão de ativação autoriza as consultas periódicas.
- Admin: modelos mostram análises e seus estados, domínios, usuários, atividades, bloqueios, notificações e verificações. Não é um console de infraestrutura: CPU, memória, tamanho da fila Redis e falhas duras de workers exigem observabilidade do servidor. Não há métricas de consumo inventadas. Configure alarmes para tarefas presas em running/pending, expiração do resultado e retenção do broker.

## Referências oficiais

- https://www.indexnow.org/documentation
- https://developers.google.com/webmaster-tools/v1/api_reference_index
- https://developers.google.com/webmaster-tools/v1/how-tos/authorizing
- https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect
- https://developers.google.com/speed/docs/insights/v5/get-started
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

O painel staff `/admin/operacao/` agrega volumes, estados persistidos, erros e uso de CPU/memória do processo web atual. Não mede os recursos de todos os workers.

HSTS preload fica desativado intencionalmente: a inclusão na lista dos navegadores exige decisão do operador e revisão de todos os subdomínios. O alerta security.W021 no check --deploy é esperado.
