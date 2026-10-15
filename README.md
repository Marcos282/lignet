# Lignet Brasil

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
