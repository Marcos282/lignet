# Lignet FTTH Designer — Etapa 1

Rota: `/ferramentas/projetista-ftth/`.
Aplicativo independente: `ftth_designer`.

## Escopo entregue

MVP visual para validação antes das etapas seguintes. Editor SVG nativo,
baseado nos mesmos padrões de interação do simulador existente, sem adicionar
React Flow ou dependências de compilação. O simulador original continua em
`/ferramentas/simulador-ftth/`, com seus arquivos e projetos locais separados.

O editor oferece OLT GPON, OLT XGS-PON, splitter assimétrico 1×2, balanceados
1×2 a 1×64, CTO, ONU/ONT, caixa de emenda e segmento de fibra. Suporta adição
por toque/clique/arraste, coordenadas editáveis, conexões por portas, distância
e parâmetros de cada fibra, movimento, zoom, ajuste à tela, duplicação sem
copiar conexões, exclusão, desfazer/refazer e salvamento temporário automático.

As saídas assimétricas possuem proporções físicas fixas: a primeira é a menor
fração selecionada, a segunda é seu complemento. É possível selecionar a porta
nos círculos do desenho ou pelo seletor nas propriedades, adequado para toque
e teclado. O editor rejeita saída ocupada, entrada duplicada, ONU como origem,
OLT como destino, porta inexistente, conexão com o próprio nó e ciclos.

Há tema claro/escuro, grade opcional, miniatura que centraliza o desenho e ajuda
contextual. Tab/Enter selecionam e conectam; setas movem componentes; Escape
cancela uma conexão e fecha os painéis; Ctrl/Cmd+Z desfaz. No celular os painéis
são recolhíveis, e Pointer Events permitem arraste e zoom por dois dedos.

## Estrutura do motor óptico

`ftth_designer/optics.py` oferece funções puras com Decimal e precisão de 40
algarismos para perdas de fibra, conectores, emendas, perdas adicionais e perda
assimétrica `-10 log10(fração) + excesso`. Perdas reais informadas substituem
as estimativas teóricas. Não há arredondamentos intermediários de exibição.

`static/ftth_designer/engine.js` mantém o esquema v1 do desenho, validação,
portas, funções numéricas equivalentes e referências iniciais editáveis:
1310 nm: 0,35; 1490 nm: 0,25; 1550 nm: 0,20 dB/km. Atenuações de 1577 e
1270 nm começam sem valor e nunca são assumidas como zero.

As perdas por saída mostradas nas propriedades são prévias do componente,
não potências recebidas. Configurações downstream/upstream, TX mínimo/máximo,
sensibilidade, sobrecarga, classe e margem já têm campos reservados e validados.
Fabricante e classe não preenchem limites automaticamente. Propagação de
potência por caminho, intervalos de TX e diagnóstico por CTO pertencem à Etapa 2.

## Persistência e próximas etapas

O salvamento desta etapa é apenas local, na chave
`lignet-ftth-designer-mvp-v1`, separado dos projetos do simulador. O desenho é
validado ao recuperar o armazenamento, limitado a 300 nós/conexões e 2 MB na
leitura. Falhas de armazenamento são informadas; não há tráfego do desenho
para o servidor. Textos são inseridos com textContent, sem HTML executável.

Não foram criados modelos, migrações ou endpoints de persistência nesta etapa.
Os modelos FTTHProject/FTTHNode/FTTHConnection/FTTHCalculation e a privacidade
por proprietário serão implementados junto da persistência na Etapa 3, após
a validação do MVP. Nenhuma configuração, credencial ou banco foi alterado.
Otimização e PDF também não são implementados antecipadamente.

## Arquivos criados

- `ftth_designer/__init__.py`, `apps.py`, `urls.py`, `views.py`.
- `ftth_designer/optics.py`, `tests.py`.
- `ftth_designer/templates/ftth_designer/editor.html`.
- `ftth_designer/static/ftth_designer/{editor.js,editor.css,engine.js}`.
- `tests/browser_designer.py` e esta documentação.

Arquivos integrados: `lignet/settings.py` (registro do app), `lignet/urls.py`
(inclusão das URLs), `templates/includes/navigation.html` (link no grupo GPON),
`core/views.py` (sitemap) e `index.html` (menu estático regenerado a partir do
componente compartilhado).

## Validação

```sh
TESTING=1 myenv/bin/python manage.py test --noinput
TESTING=1 myenv/bin/python manage.py makemigrations --check --dry-run
TESTING=1 myenv/bin/python manage.py build_portal_navigation --check
```

Para o navegador, inicie uma instância local de desenvolvimento:

```sh
TESTING=1 DEBUG=true myenv/bin/python manage.py runserver 127.0.0.1:8101 --noreload
python tests/browser_designer.py
```

O teste de navegador requer Playwright e Chrome, sem dependência de produção.
`LIGNET_PREVIEW_URL` permite alterar a URL local. São verificadas larguras de
320, 375, 768, 1024 e 1920 px, portas, proporções, validação de ciclos, histórico,
edição de distância, salvamento/recuperação, arraste, zoom por toque e ausência
de rolagem horizontal. Evidências em `/tmp/lignet-designer-qa/`.
Testes Chromium com toque não substituem validação em Safari/iPhone físico.

## Implantação após validação visual

A alteração ainda requer publicação pelo fluxo Git habitual, collectstatic e
recarga apenas da aplicação web Lignet. Esta etapa não requer migrate, novos
serviços ou alteração do Nginx. Não usar TESTING em produção. As etapas
seguintes não devem começar automaticamente antes da validação deste MVP.
