# Lignet Brasil

## Blog com publicação automática

O blog Django, lote inicial de 20 guias, fotos próprias, paginação, agendamentos
e rotina Cron estão documentados em [Blog editorial](docs/BLOG.md).
Após migrar, execute `python manage.py blog_seed`, cadastre as fotos no admin
e habilite a rotina. Aprovação é automática; retirada é manual. Não há fotos
de terceiros nem publicação de textos sem capa autorizada.

Site estático: abra `index.html` no navegador ou publique esta pasta em um
servidor HTTP. Não exige Node.js, build, conta ou API externa.

## Gerador de QR Code

- Acesso pelo botão "Criar QR Code" ou pela seção `#qrcode`.
- Aceita texto e links, incluindo acentos e emojis, até 1.000 bytes em UTF-8.
- Gera PNG de 512 ou 1.024 pixels, com correção de erros M e margem branca
  mínima de quatro módulos. Para links, informe o protocolo `https://`.
- Editar o conteúdo ou o tamanho invalida a prévia anterior para evitar baixar
  um código desatualizado.
- Todo o processamento é local, inclusive quando aberto sem conexão.
- Biblioteca `qrcode-generator` **2.0.4**, de Kazuhiko Arase, distribuída sob
  licença MIT em `vendor/`. Os arquivos `qrcode.js` e `qrcode_UTF8.js` vieram
  da distribuição npm:
  https://registry.npmjs.org/qrcode-generator/-/qrcode-generator-2.0.4.tgz
- Ao publicar, mantenha `qr.js` e a pasta `vendor/` ao lado de `index.html`.

Antes de distribuir ou imprimir, confira a leitura do QR Code com uma câmera.

### Verificações

Foram conferidos no navegador: decodificação independente com jsQR 1.4.0 de
URL, texto com acentos e emoji e conteúdo no limite de 1.000 bytes; leitura
do PNG exportado; dimensões de 512 e 1.024 pixels; rejeição de texto vazio e
acima do limite; invalidação da prévia após edição; layout de 375 pixels.
O decoder usado nos testes não é uma dependência do site.

Para repetir a conferência funcional, gere códigos dos dois tamanhos e leia
os PNGs com outro leitor. Verifique também que editar o texto esconde o
download anterior e que as ferramentas IP/CIDR e de imagens continuam operando.

## Lignet SEO — aplicação Django

O portal estático acima continua funcionando. As novas ferramentas de servidor
estão em uma aplicação Django separada por apps, no mesmo repositório.
Requisitos: Python 3.12, PostgreSQL e Redis. Não use TESTING em produção.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
# Se .env ainda não existir, crie-o a partir de .env.example.
# Preencha SECRET_KEY, banco, domínio e credenciais opcionais.
.venv/bin/python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
.venv/bin/python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py check --deploy
```

Guarde as chaves geradas em SECRET_KEY e TOKEN_ENCRYPTION_KEY, respectivamente.
Não versione o `.env`. Para desenvolvimento local, use DEBUG=true,
ALLOWED_HOSTS=localhost,127.0.0.1 e SITE_URL=http://127.0.0.1:8000.
PostgreSQL é o banco padrão; SQLite em memória é usado somente em testes.

Execute em terminais ou serviços separados, com o mesmo ambiente:

```bash
.venv/bin/python manage.py runserver
.venv/bin/celery -A lignet worker --loglevel=INFO --concurrency=2
.venv/bin/celery -A lignet beat --loglevel=INFO
```

Acesse `/ferramentas/seo/` para analisar sem cadastro e `/painel/` para domínios,
IndexNow, Google Search Console e monitoramento. O portal original fica em `/`.
As análises dependem dos workers. Nenhuma notificação IndexNow ou conexão Google
é executada na instalação ou durante os testes.

Teste isolado, sem banco externo, Redis ou APIs:

```bash
TESTING=1 .venv/bin/python manage.py test
TESTING=1 .venv/bin/python manage.py makemigrations --check --dry-run
```

Para produção, use Gunicorn atrás do Nginx TLS existente. Exemplos opcionais
estão em `deploy/`; não foram aplicados ao servidor. Caso use Docker Compose,
configure `.env`, crie as pastas de static e migre explicitamente antes de iniciar:

```bash
docker compose --env-file .env -f deploy/compose.yaml build
docker compose --env-file .env -f deploy/compose.yaml run --rm web python manage.py migrate
docker compose --env-file .env -f deploy/compose.yaml run --rm web python manage.py collectstatic --noinput
docker compose --env-file .env -f deploy/compose.yaml up -d
```

O volume `static` deve ser servido pelo Nginx. Configure a rede de saída dos
workers antes de expor a ferramenta pública. Leia [implementação e limites](docs/IMPLEMENTACAO.md)
para critérios de pontuação, configuração OAuth, firewall, operação e dependências
que precisam ser validadas no ambiente de produção.

## Lignet Global Ping

Nova ferramenta em `/ferramentas/ping-mundial/`, com ping, traceroute, DNS e HTTP
via API oficial Globalping, mapa Leaflet/OpenStreetMap e histórico temporário.
Não usa token nem créditos pagos. Celery executa as medições; Redis controla
limites, cache e cotas compartilhadas. Os limites são ajustáveis no admin.

Na implantação autorizada, aplique `python manage.py migrate globalping`,
execute `collectstatic` e atualize os workers/Beat. Nenhum serviço ou banco
existente foi modificado automaticamente. O proxy precisa encaminhar também
`/api/globalping/` ao Django. Consulte [instalação e operação do Global Ping](docs/GLOBALPING.md)
para todos os parâmetros, requisitos de rede, privacidade e testes.
