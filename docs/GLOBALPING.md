# Lignet Global Ping

## Instalação no projeto existente

A implementação usa o Django, PostgreSQL, Redis e Celery já previstos no projeto. Nenhum token Globalping é necessário: todas as chamadas são anônimas e gratuitas. Nenhuma configuração de Nginx/Gunicorn, banco de produção ou `.env` existente foi alterada.

1. Atualize as dependências com `pip install -r requirements.txt` no ambiente virtual do projeto.
2. Adicione ao ambiente, se quiser mudar os padrões, as variáveis `GLOBALPING_*` documentadas em `.env.example`. Não substitua seu `.env`.
3. Revise e aplique a nova migração em uma janela autorizada: `python manage.py migrate globalping`. Não há migração de dados existentes.
4. Colete os estáticos: `python manage.py collectstatic --noinput`.
5. Reinicie os processos da aplicação/Celery conforme seu procedimento de implantação. Mantenha um único Celery Beat. Os novos agendamentos verificam tarefas abandonadas a cada minuto e removem histórico expirado a cada hora.
6. Abra `/ferramentas/ping-mundial/`. No admin, adicione a configuração em **Lignet Global Ping → Limites do Lignet Global Ping** para personalizar os limites. Os padrões do ambiente valem enquanto esse registro não for salvo.

Os caminhos `/ferramentas/` já previstos no exemplo Nginx cobrem as páginas. Os endpoints novos são `/api/globalping/`: se seu proxy só encaminha uma lista explícita de rotas Django, o operador deverá incluir esse prefixo na publicação. Nenhuma alteração foi aplicada automaticamente. Os endpoints aceitam os cookies de sessão e o token CSRF do próprio portal; não habilite CORS público nem acesso direto ao Gunicorn. As páginas usam Leaflet local e o Bootstrap já adotado pelo portal.

## Páginas e endpoints

- `/ferramentas/ping-mundial/`: ping online / latência internacional.
- `/ferramentas/traceroute-mundial/`: rotas e saltos por localidade.
- `/ferramentas/dns-mundial/`: comparação A, AAAA, MX, NS, TXT e CNAME.
- `/ferramentas/http-mundial/`: HEAD HTTP/HTTPS, tempos e status.
- `POST /api/globalping/medicoes/`: JSON `target`, `kind`, `locations` (lista como `country:BR`, `continent:EU` ou `world` sozinho), `probes`, `record_type` e `authorized: true`. Exige CSRF; retorna 202 com UUID local.
- `GET /api/globalping/medicoes/{uuid}/`: estado/resultados locais da sessão ou proprietário. Nunca consulta a API externa diretamente.
- `GET /api/globalping/historico/`: até 20 medições locais ainda válidas.

Os quatro títulos, descrições e canonicals são próprios; cada página tem dados estruturados WebApplication, conteúdo explicativo e links entre as ferramentas. O sitemap público inclui essas páginas e exclui os endpoints/históricos. APIs usam noindex e no-store, inclusive em erros de rota. A visualização requer JavaScript.

## Fluxo e contrato oficial

O formulário valida sintaxe, autorização declarada e limites. Um registro local é criado e uma tarefa Celery faz a resolução DNS e bloqueia destinos locais/privados/reservados, inclusive respostas DNS mistas. Nomes DNS sem A/AAAA são aceitos somente no teste DNS, para permitir consultas de MX/TXT, mas nomes internos e endereços privados continuam proibidos. IPv6 público é aceito; seu suporte nas sondas é experimental. IPs de transição/mapeados não são aceitos.

O worker envia `POST https://api.globalping.io/v1/measurements`, com os tipos oficiais `ping`, `traceroute`, `dns` ou `http`. Usa `limit` global, filtros documentados `country`/`continent`, `inProgressUpdates: true` e `timeout: 30`. Não aceita opções arbitrárias, resolvers customizados, cabeçalhos de usuário ou portas customizadas. HTTP aceita domínio/IP ou URL sem query string; usa `measurementOptions.protocol` e `request.method: HEAD`, com caminho opcional. Ping usa três pacotes por sonda. A resposta 202 fornece `id` e `probesCount`; não presumimos que todas as sondas pedidas estejam disponíveis.

Cada tarefa de consulta executa apenas um GET ao ID validado no host fixo da API, guarda o resultado e agenda a próxima tarefa com countdown. Não há sleeps ou polling externo no processo web. ETags são reenviados por If-None-Match; 304 preserva os dados anteriores. O intervalo padrão é de dois segundos após a resposta, com proteção contra entregas duplicadas. Qualquer estado remoto diferente de `in-progress` encerra as consultas, conforme orientação oficial. Cada sonda mantém seu próprio status; uma medição concluída pode conter sondas com falha.

POST não é repetido automaticamente: um timeout pode ocultar uma criação aceita pelo serviço. Em caso de 429 na criação, novos envios respeitam a pausa global em Redis e a interface informa o erro/tempo de espera. Em GET, 429 agenda a próxima consulta respeitando Retry-After, dentro do prazo total. Erros transitórios, respostas inválidas, limite de corpo de 2 MB e timeouts encerram a tentativa com mensagem; resultados parciais já salvos são preservados.

## Cotas e custos

Na especificação oficial consultada em 15/10/2026, o modo anônimo oferece 250 testes de sonda/hora por IP e até 50 sondas por medição; a consulta de resultados tem teto de duas requisições por segundo por medição. Autenticação oferece limites diferentes e pode gastar créditos depois da cota gratuita. **Esta implementação não envia Authorization nem usa tokens, portanto não acessa créditos pagos.** Não há cobrança aos visitantes.

Os padrões locais são 10 inícios/IP/usuário/hora, 5 sondas por medição e orçamento compartilhado de 200 sondas/hora. Os tetos administrativos são 50 sondas e 250 testes/hora, mesmo se houver uma configuração inválida no banco. Cada tentativa reserva o total solicitado antes do POST. Reservas recusadas ou falhas não são devolvidas: essa decisão conservadora evita reutilizar cota de uma criação cujo resultado seja incerto. Os contadores Redis usam incremento atômico e janela de uma hora a partir da primeira solicitação. Eles não substituem a cota real da Globalping, que pode ser compartilhada com outros sistemas sob o mesmo IP de saída.

O admin também permite desativar a ferramenta, ajustar frequência de leitura local, intervalo de polling, prazo de execução, duração do cache e retenção do histórico. Consumo, restante, limite e reset ficam nulos se os cabeçalhos oficiais não estiverem presentes. Nunca estimamos consumo real a partir da quantidade pedida. Os registros guardam o uso retornado na criação; os limites exibidos são uma fotografia daquele instante. Redis indisponível bloqueia novos testes, em vez de permitir uso ilimitado. Configure corretamente TRUSTED_PROXY_IPS/X-Real-IP, como descrito na documentação geral, para rate limiting por visitante atrás do proxy.

## Cache e privacidade

Resultados finais são reutilizados por cinco minutos por padrão, conforme payload normalizado completo (tipo, alvo, opções, localidades e limite). Cache é compartilhado apenas para essas medições públicas; o histórico local, UUID e proprietário são independentes. A interface sinaliza a reutilização e conserva a data original de createdAt retornada pela API, quando disponível. Uma reutilização tem consumo zero e não cria teste remoto. DNS e bloqueios do administrador são verificados antes de reutilizar o cache.

O histórico é acessível pela sessão criadora, inclusive após rotação de sua chave no login, ou conta proprietária. UUIDs de outras sessões retornam 404. A retenção padrão é 24 horas; dados expirados deixam de ser acessíveis imediatamente e são removidos pelo Beat até uma hora depois. Sem Beat, execute periodicamente `python manage.py globalping_cleanup`. Alterações na retenção aplicam-se a novos testes. Logs de atividade existentes usam o UUID local e estado; não guardam IPs crus dos visitantes. Os contadores de IP usam hashes em Redis.

A Globalping recebe alvo e parâmetros e torna medições públicas, possivelmente descobertas/publicadas por terceiros, tipicamente por até seis meses. A retenção local não remove resultados remotos. O formulário explica isso e pede autorização declarada. Não envie segredos, dados de clientes ou parâmetros sensíveis. Nenhum alvo é conectado diretamente pelo servidor Django: as conexões são realizadas pelas sondas do provedor, que também bloqueiam destinos privados. A validação DNS local é uma camada adicional; ela não fixa o IP usado em cada resolvedor remoto. Não prometemos a mesma resolução em todos os países.

## Interpretação dos resultados

Somente campos presentes nas respostas são mostrados. Ausentes aparecem como “—”; zero permanece zero. Sem resultados, não há marcadores de sondas. O mapa localiza a origem, não o destino nem os roteadores. Não desenhamos rotas geográficas inferidas.

Ping mostra stats.min/avg/max/loss. Traceroute lista a ordem dos hops, resolvedAddress/Hostname e cada RTT; sem timings há “Sem resposta”. DNS mostra answers, statusCodeName, resolver e timings.total. A comparação usa conjuntos de registros (nome, tipo, classe e valor) e código DNS, ignorando TTL e ordem; precisa de pelo menos duas respostas finais. Diferenças podem ser normais por geolocalização e cache. HTTP mostra statusCode, timings, TLS e o cabeçalho Location informado; não existe parâmetro de follow-redirects nesta interface e não fabricamos uma cadeia de saltos HTTP. A saída técnica fica em texto, nunca como HTML executável.

## Mapa e licença

Leaflet 1.9.4 é distribuído localmente em `static/vendor/leaflet/`, com sua licença BSD-2-Clause. A configuração padrão usa `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, atribuição visível OpenStreetMap, Referer permitido e o cache normal do navegador. Não há proxy de tiles, prefetch, download em lote nem modo offline. O mapa inicial e as movimentações solicitadas pelo usuário carregam somente o viewport normal. Para tráfego elevado ou indisponibilidade, use um provedor adequado alterando GLOBALPING_TILE_URL e GLOBALPING_TILE_ATTRIBUTION e respeite suas condições/licença. As tabelas funcionam mesmo se o serviço de mapas falhar.

## Verificação

```bash
TESTING=1 .venv/bin/python manage.py test
TESTING=1 .venv/bin/python manage.py makemigrations --check --dry-run
```

Os testes simulam API e não consomem a cota externa. Cobrem tipos e filtros, SSRF/entradas, propriedade de sessão/conta, CSRF, cotas por IP/usuário e globais, cache, POST sem retry, polling, ETag, 429, falhas, normalização, administração e expiração. Para QA opcional do navegador, instale Playwright em um ambiente de desenvolvimento, inicie um servidor local de teste e execute `tests/browser_globalping.py`. O script usa Chrome instalado, respostas simuladas e tiles substituídos; não dispara medições nem baixa tiles. Capturas são salvas em `/tmp/lignet-globalping-qa/`.

Validação desta entrega: 99 testes automatizados passaram em SQLite e PostgreSQL temporário; interface conferida em 1440 px e 390 px para os quatro tipos, sem erros JavaScript ou overflow horizontal. Uma verificação real usou uma sonda BR e um único pacote de ping ao domínio oficial globalping.io; criação 202, medição concluída, consumo oficial de uma unidade, sem autenticação. Dados desse teste não são fixtures de produção.

## Referências oficiais

- API e esquema: https://globalping.io/docs/api.globalping.io e https://api.globalping.io/v1/spec.yaml
- Código e política de resultados públicos: https://github.com/jsdelivr/globalping
- Segurança das sondas: https://github.com/jsdelivr/globalping-probe
- Leaflet: https://leafletjs.com/reference.html
- Política de tiles: https://operations.osmfoundation.org/policies/tiles/
