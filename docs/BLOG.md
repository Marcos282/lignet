# Blog editorial da Lignet Brasil

## Comportamento

- Blog público em `/blog/`, categorias e URLs de artigos com slugs.
- 20 guias originais em português, sem coleta de notícias para esse primeiro lote.
  Os textos explicam as ferramentas reais, trazem limites e referências públicas.
- **Aprovação/publicação automática por padrão; retirada somente pelo painel.**
  Não há publicação sem capa própria autorizada. Os textos aguardam a biblioteca
  de fotos quando não houver imagem da categoria disponível.
- Rotina desabilitada até o operador concluir instalação, fotos e horários.
  Configuração de 1 a 20 artigos por dia, tamanho de página de 1 a 50 e horário
  inicial da geração. Valores iniciais: 3 por dia, 6 por página, geração às 06h.
- Horários de publicação iniciais: 09h, 13h e 18h no `TIME_ZONE` do Django
  (`America/Araguaina` no projeto). Ajuste antes de habilitar.
- A aprovação automática reserva o próximo horário disponível dentro do limite
  diário. O lote de 20 pode ser distribuído por vários dias; criar 20 não significa
  publicar todos imediatamente. Para mais publicações no mesmo dia, configure
  também mais horários, além do limite.
- O Cron verifica publicações vencidas a cada cinco minutos; a precisão é de
  cinco minutos, não de segundos. Interrupções podem atrasar publicações.

## Instalação nativa no servidor

Faça backup do banco do Lignet antes de migrar. Não altere o Novainfo.
Na pasta do projeto atualizado:

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py check
.venv/bin/python manage.py migrate --plan
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py blog_seed
```

`blog_seed` é idempotente: cria os 20 guias uma vez sem sobrescrever textos
editados ou restaurar os retirados. Não acessa feeds, Ollama nem APIs.
Os artigos são persistidos no banco ao executar esse comando; o código não
executa a carga nem migrações automaticamente ao iniciar o servidor.

Não use `TESTING=1` em produção: ele seleciona SQLite em memória.
Recarregue o **serviço próprio do Lignet** depois de atualizar o código.
O processo da porta 8001 identificado anteriormente pertence ao Novainfo,
não ao Lignet. Confirme o serviço e a porta atuais antes de alterar o proxy.

## Fotos próprias

Abra `/admin/blog/photo/` e envie fotos por categoria:

- Redes e conectividade;
- Endereçamento IP;
- Imagens e desempenho;
- Produtividade digital;
- SEO e presença digital.

Preencha descrição acessível, autor/crédito, confirmação de direitos e uso
automático. Não marque a confirmação para fotos de terceiros sem autorização.
As fotos genéricas podem ser reutilizadas em artigos da mesma categoria;
escolhemos primeiro as menos utilizadas. A legenda identifica o caráter
ilustrativo, sem sugerir registro de um evento.

JPG, PNG e WebP são aceitos até 8 MB, 24 megapixels e 12.000 pixels por lado.
A aplicação reexporta para JPEG de até 1.920 pixels, descarta o nome original
e não preserva EXIF/localização. Fotos e créditos são editáveis no painel.
O lote inicial não inclui fotos de terceiros nem imagens falsas de acontecimentos.

Guarde `media/` em armazenamento persistente e faça backup. Configure acesso
somente de escrita para o usuário do serviço. Fotos antigas substituídas não
são apagadas automaticamente, para evitar remover um arquivo ainda em uso.

## Nginx e rotas

Mescle no bloco HTTPS existente, sem substituir os certificados ou outros sites:

```nginx
client_max_body_size 10m;

location /static/ {
    alias /var/www/lignetbrasil/site/staticfiles/;
    autoindex off;
}

location /media/ {
    alias /var/www/lignetbrasil/site/media/;
    autoindex off;
    add_header X-Content-Type-Options nosniff always;
}
```

Acrescente `blog` à expressão de rotas encaminhadas ao Gunicorn do Lignet:

```nginx
location ~ ^/(blog|ferramentas|api/globalping|relatorios|painel|conta|dominios|integracoes|admin)/ {
    proxy_pass http://127.0.0.1:8003;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
}
```

A porta 8003 deve ser conferida no servidor antes de usar o exemplo. Preserve
o tratamento especial do callback Google com `access_log off`, os bloqueios
de arquivos ocultos e as rotas de sitemap/robots já existentes.
Teste `sudo nginx -t` antes de `sudo systemctl reload nginx`.

## Ollama e fontes

O processo diário usa o endpoint oficial `/api/chat` de um Ollama **local**:

```dotenv
BLOG_OLLAMA_URL=http://127.0.0.1:11434
BLOG_OLLAMA_MODEL=qwen2.5:7b
```

Instale o Ollama pelo procedimento oficial para o seu sistema, escolha um
modelo compatível com a memória disponível e baixe-o, por exemplo:

```bash
ollama pull qwen2.5:7b
ollama list
```

Ollama deve estar ouvindo somente em loopback. Não abra sua porta para a internet.
O modelo é configurado por ambiente, não por texto vindo de feeds ou usuários.
A instalação real do Ollama/modelo não foi realizada por esta implementação.
O cliente limita a resposta a 1 MB, o contexto e a saída solicitada ao modelo,
com timeout de conexão/leitura; hardware insuficiente pode causar falhas.

No admin de fontes, cadastre RSS/Atom de fontes que você tenha autorização para
utilizar editorialmente. Confira os termos e marque a autorização explicitamente.
Nenhuma fonte vem com autorização presumida. Até 30 feeds e 50 itens por feed
são lidos por execução diária, usando o cliente HTTP público protegido do projeto.
`feedparser` recebe os bytes, nunca uma URL para buscar por conta própria.
BeautifulSoup extrai texto simples do título/resumo; não fazemos cópia do corpo
das notícias nem download de suas imagens.

A seleção considera termos inteiros normalizados, categoria e relação com
ferramentas reais. O método é heurístico e auditável, não um classificador
treinado. Pautas sem termos relacionados às ferramentas recebem score zero.
Links normalizados são deduplicados por hash. Resumos ficam limitados a 1.400
caracteres. Feeds, redirecionamentos e DNS usam os bloqueios SSRF existentes.

O prompt solicita um guia educativo original, não uma reescrita de notícia.
Feed é tratado como entrada não confiável, sem acesso a ferramentas. Retornos
fora do contrato, cópias extensas do resumo e títulos muito semelhantes a textos
já existentes são recusados. **Essas verificações não comprovam veracidade nem
originalidade absoluta.** Textos gerados recebem aviso público de auxílio de IA,
referência à fonte e recomendação de confirmação independente. A publicação
automática não é revisão factual humana e pode produzir erros.

## Cron e operação

Execute como o mesmo usuário do serviço, com o mesmo `.env`:

```bash
.venv/bin/python manage.py blog_run
```

No painel `/admin/blog/editorialsettings/`, habilite a rotina após cadastrar
fotos, fontes e horários. Mantenha publicação automática ativada.
O primeiro lote pode ser agendado mesmo sem fontes ou Ollama, pois os 20 guias
já foram preparados. Geração diária nova depende desses dois componentes.

Crie uma pasta de logs protegida, de propriedade do usuário do serviço. Copie
a entrada de [blog.cron.example](../deploy/blog.cron.example) para `crontab -e`,
ajustando caminhos. O Cron deve executar `blog_run` a cada cinco minutos.
Configure rotação e monitore retornos diferentes de zero e execuções sem término.

Há lock de arquivo por projeto e lock de sessão PostgreSQL contra sobreposição.
Um lote de geração é reservado por dia. Uma falha ou encerramento depois dessa
reserva não reenvia o lote automaticamente no mesmo dia: consulte o histórico,
corrija a causa e deixe o próximo ciclo diário processar pautas novas. Pautas
com erro permanecem como `failed`; podem ser examinadas no admin e recolocadas
em `found` pelo operador para uma tentativa posterior.

As publicações já agendadas são verificadas mesmo quando a geração daquele
dia já ocorreu. O limite diário também é aplicado na publicação, inclusive
para atrasos acumulados. Artigos retirados manualmente nunca são recolocados
na fila automaticamente. A rotina não exclui artigos ou histórico.

Em Docker, há volume persistente `media`. O exemplo de Cron acima é para
implantação nativa: `127.0.0.1` dentro de um contêiner não é o host. Não aponte
o Cron nativo para uma instalação containerizada sem ajustar ambiente,
armazenamento e disponibilização local do Ollama.

## Painel e retirada

- `/admin/blog/indicadores/`: seis indicadores, execuções e eventos paginados.
- `/admin/blog/article/`: textos, fotos, categorias, palavras-chave e agendamentos.
- Ação **Retirar manualmente**: esconde artigo, remove-o do sitemap e bloqueia
  republicação automática; preserva texto e histórico. Exclusão física de artigos
  pelo admin é desabilitada.
- Edições de artigos ativos retornam ao fluxo automático; retirados continuam
  retirados. Há modo manual opcional, mas ele não é o padrão pedido.
- Staff precisa da permissão de visualização de artigo para os indicadores.
  A permissão `blog.approve_article` permite a ação de retirada/aprovação.

## Google e SEO

As páginas públicas têm canonical, descrição, Open Graph, capa e BlogPosting
com datas reais, autor institucional, categoria, referências e palavras-chave.
Textos são escapados e dados estruturados não aceitam injeção de HTML.
Artigos relacionados usam categoria/palavras-chave; ferramentas usam termos
do título/texto, com links reais para ping, CIDR, DNS, SEO, imagens e QR Code.

`/blog/sitemap.xml` é um índice; os sitemaps de artigos e categorias são
paginados em até 1.000 URLs. Apenas publicações já disponíveis entram no índice.
O sitemap do portal aponta para a listagem do blog e o robots anuncia ambos.

Reutilizamos a integração Search Console existente. No painel editorial,
a conta proprietária com domínio verificado pode enviar o sitemap do blog
e atualizar os dados via formulário protegido por CSRF. Configure OAuth,
chave de criptografia e Celery conforme a documentação existente.
Não criamos outro fluxo OAuth nem enviamos dados ao Google sem a ação autorizada.
Google não garante indexação, tráfego ou posição por envio de sitemap ou uso de IA.

## Validação

```bash
TESTING=1 .venv/bin/python manage.py test blog tests globalping
TESTING=1 .venv/bin/python manage.py makemigrations --check --dry-run
```

Os testes usam banco em memória, arquivos temporários e respostas externas
simuladas. Não alteram o PostgreSQL de produção nem geram chamadas reais ao
Ollama, Google ou Globalping. Confira no servidor após implantar: fotos, CSS,
paginação, uma publicação agendada, retirada manual, execução Cron e logs.
