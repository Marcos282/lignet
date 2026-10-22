# Simulador FTTH

Ferramenta pública em `/ferramentas/simulador-ftth/`, integrada à categoria
**Ferramentas → Fibra Óptica / GPON**. A rota Django renderiza o editor, sem
modelos, migrações, cadastro, APIs ópticas ou chamadas a equipamentos.

## Organização

- `static/ftth/engine.js`: esquema de projeto v1, validação, capacidades,
  perfis de referência e cálculos, independentes da interface.
- `static/ftth/editor.js`: editor SVG, Pointer Events, zoom, histórico,
  propriedades, localStorage, arquivos JSON e relatório.
- `static/ftth/editor.css`: três painéis no desktop, componentes recolhíveis,
  propriedades inferiores, controles compactos e resultados em cartões no celular.
- `templates/ftth.html`: interface, acessibilidade e integração com o template base.

Não há dependências JavaScript adicionais. Usa APIs de navegadores modernos:
ES modules, Pointer Events, ResizeObserver, structuredClone, SVG e localStorage.

## Uso

Adicione componentes com os botões, pela paleta ou por arraste. No celular,
**Componentes** abre a paleta. O menu **Editar** oferece Conectar, Mover,
Excluir, Desfazer e Refazer; **Visualização** controla zoom e centralização;
**Projeto** reúne os arquivos e o relatório.

No modo Conectar, selecione a origem e depois o destino. A seleção da origem
pelo cartão usa a primeira saída livre. As saídas também estão representadas
individualmente no SVG; para escolher uma saída por toque ou teclado, abra as
propriedades da origem, escolha o número e pressione **Conectar esta saída**.
A seleção de uma linha abre suas propriedades de distância e perdas.

Tab navega pelos componentes e conexões; Enter seleciona/conecta; setas movem
um componente em passos de dez unidades. Escape cancela a conexão pendente e
fecha os painéis móveis. Ctrl/Cmd+Z desfaz e Ctrl/Cmd+Shift+Z ou Ctrl/Cmd+Y refaz.
Arrastar o fundo move a visão; dois dedos alteram o zoom.

## Modelo óptico

Cada ONU tem um único caminho até uma OLT. A potência é TX menos a soma das
perdas daquele caminho, excluindo as ramificações irmãs. Os sentidos usam TX,
sensibilidade, sobrecarga, perdas dos componentes e atenuação da fibra
separadamente. As perdas da fibra incluem km × dB/km, conectores × perda,
fusões × perda e perdas adicionais. Trechos podem ser representados por uma
conexão ou por um componente de fibra; se ambos forem preenchidos, ambos
entram no orçamento. Evite representar o mesmo trecho duas vezes.

Quando existe uma porta PON, ela é o receptor upstream. Seu TX downstream,
quando preenchido, substitui o TX do chassi OLT; a ligação OLT → PON é lógica
(e suas distâncias/perdas não integram o caminho óptico). O caminho de fibra
começa na porta. Sem uma porta explícita, configure a óptica na OLT.

A margem disponível é `min(RX − sensibilidade, sobrecarga − RX)`.

- Vermelho: RX fora dos limites do receptor.
- Amarelo: RX dentro dos limites, mas folga menor que a margem configurada.
- Verde: RX dentro dos limites e folga suficiente em ambos os extremos.
- Cinza: caminho sem OLT, TX ausente ou limites do receptor ausentes.

Os limites e TX começam vazios. Classe, fabricante e modelo são metadados de
referência e não atribuem limites automaticamente. Perfis futuros podem ser
adicionados a `PROFILES`, mantendo os valores dependentes do módulo utilizado.
As perdas iniciais dos splitters seguem a especificação do projeto e são
editáveis por sentido. Atenuações, conectores, fusões e o exemplo são referências
ilustrativas editáveis; confira os dados do fabricante. Alterar λ não estima
uma curva espectral: atualize também a atenuação para a fibra utilizada.

O editor permite componentes desconectados durante a construção, mas os
identifica como sem entrada. Eles nunca produzem um caminho válido até a OLT.
Conexões circulares, segunda entrada, saída ocupada, ONU como origem e
capacidade excedida são rejeitadas, inclusive na importação.

## Persistência e relatório

**Salvar local** grava um projeto no navegador (`lignet-ftth-v1`).
**Abrir local** recupera esse projeto e permite desfazer a substituição.
Exportar JSON cria uma cópia portátil com parâmetros, coordenadas e conexões.
Importar valida todo o projeto antes de substituir o atual, limita o arquivo
a 2 MB e o grafo a 500 componentes/conexões. Dados são tratados como texto,
sem `eval`, HTML importado ou execução de código. Somente campos conhecidos
são copiados. Conteúdo inválido deixa o projeto atual intacto.

**Relatório / PDF** usa a impressão nativa: escolha **Salvar como PDF**.
O relatório contém diagrama vetorial, data no horário de Brasília, sentido, configurações,
quantidades, resultados por ONU, distância óptica por caminho, margens,
alertas e parâmetros. A folha de impressão oculta a interface do editor.
O relatório identifica os valores como estimativas, não medições.

## Verificação

```sh
TESTING=1 myenv/bin/python manage.py test --noinput
TESTING=1 DEBUG=true myenv/bin/python manage.py runserver 127.0.0.1:8098 --noreload
```

Em outro terminal, com Playwright disponível e Chrome instalado:

```sh
python tests/browser_ftth.py
```

A URL pode ser substituída pela variável `LIGNET_PREVIEW_URL`.
Os testes de navegador carregam `tests/ftth_engine_cases.js` por interceptação
local. Exercitam 34 verificações do motor e o fluxo de interface a 320, 375,
768, 1024 e 1920 px, incluindo arraste, pan, pinch por eventos de toque do
Chromium, arquivos, diagnóstico, histórico e PDF. Os artefatos de QA ficam em
`/tmp/lignet-ftth-qa/`. Não equivalem a testes em Android/iPhone físicos ou Safari.

A implantação usa o fluxo normal do projeto para código Django e arquivos
estáticos. O simulador não requer alterações no Nginx nem novos serviços.

## Atualização de uma implantação existente

`git pull` atualiza os arquivos; não recarrega o processo Django/Gunicorn nem
copia os novos arquivos para `STATIC_ROOT`. Se a rota nova retornar 404, páginas
internas ainda mostrarem o menu antigo e `/static/ftth/editor.js` retornar 404,
confira o commit no diretório usado pelo processo, execute `collectstatic` no
mesmo ambiente e recarregue somente o serviço web do Lignet. Nenhuma migração
de banco é necessária para esta ferramenta. Não é necessário substituir Nginx.

Se a implantação usa o Compose fornecido pelo projeto, execute da raiz:

```sh
git pull --ff-only
docker compose --env-file .env -f deploy/compose.yaml build web
docker compose --env-file .env -f deploy/compose.yaml run --rm web python manage.py collectstatic --noinput
docker compose --env-file .env -f deploy/compose.yaml up -d --no-deps web
```

Com Gunicorn/systemd, use o Python do ambiente virtual efetivamente usado pelo
serviço para executar `manage.py collectstatic --noinput`; depois reinicie
somente a unidade web do Lignet, com o nome confirmado no servidor. Não adivinhe
o nome da unidade e não reinicie todos os serviços Gunicorn da máquina.

A página inicial pode ser entregue diretamente pelo Nginx como `index.html`.
Ela contém uma versão gerada do mesmo menu, com CSS e JavaScript incorporados,
para funcionar mesmo sem passagem pelo Django e sem depender de `/static/`.
Ao alterar o menu compartilhado, sincronize esse artefato antes de versionar:

```sh
TESTING=1 myenv/bin/python manage.py build_portal_navigation
TESTING=1 myenv/bin/python manage.py build_portal_navigation --check
```

O Django substitui somente esse bloco ao servir `/`, preservando a opção de
conta autenticada. O gerador preserva o conteúdo e o bloco de Analytics do portal.

Depois da implantação, confirme HTTP 200 na ferramenta e nos dois recursos:
`/ferramentas/simulador-ftth/`, `/static/ftth/editor.js` e
`/static/lignet/navigation.css`. A página inicial deve conter `id="site-nav"`
exatamente uma vez.
