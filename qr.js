(() => {
  const form = document.querySelector("#qr-form");
  const content = document.querySelector("#qr-content");
  const size = document.querySelector("#qr-size");
  const error = document.querySelector("#qr-error");
  const canvas = document.querySelector("#qr-canvas");
  const download = document.querySelector("#qr-download");
  const status = document.querySelector("#qr-status");

  function clearResult() {
    canvas.classList.add("hidden");
    download.classList.add("hidden");
    download.removeAttribute("href");
    error.classList.add("hidden");
    status.textContent = "Preencha o conteúdo e clique em Gerar QR Code.";
  }

  content.addEventListener("input", clearResult);
  size.addEventListener("change", clearResult);

  form.addEventListener("submit", event => {
    event.preventDefault();
    clearResult();
    try {
      if (!content.value.trim()) throw new Error("Digite um link ou texto para gerar o QR Code.");
      if (new TextEncoder().encode(content.value).length > 1000) {
        throw new Error("O conteúdo excede 1.000 bytes. Reduza o texto ou use um link mais curto.");
      }
      if (typeof qrcode !== "function") {
        throw new Error("O gerador não carregou. Recarregue a página e verifique os arquivos da ferramenta.");
      }
      const qr = qrcode(0, "M");
      qr.addData(content.value, "Byte");
      qr.make();
      const dimension = Number(size.value);
      if (![512, 1024].includes(dimension)) throw new Error("Selecione um tamanho válido para o PNG.");
      const modules = qr.getModuleCount();
      // Integer-sized modules and at least four white modules prevent blurry edges.
      const cellSize = Math.floor(dimension / (modules + 8));
      const offset = Math.floor((dimension - modules * cellSize) / 2);
      canvas.width = canvas.height = dimension;
      const context = canvas.getContext("2d");
      if (!context) throw new Error("Seu navegador não permite desenhar o QR Code.");
      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, dimension, dimension);
      context.fillStyle = "#000000";
      for (let row = 0; row < modules; row++) {
        for (let col = 0; col < modules; col++) {
          if (qr.isDark(row, col)) {
            context.fillRect(offset + col * cellSize, offset + row * cellSize, cellSize, cellSize);
          }
        }
      }
      download.href = canvas.toDataURL("image/png");
      canvas.classList.remove("hidden");
      download.classList.remove("hidden");
      status.textContent = `QR Code pronto · ${dimension} × ${dimension} px`;
    } catch (cause) {
      error.textContent = cause instanceof Error ? cause.message : "Não foi possível gerar o QR Code. Tente um texto mais curto.";
      error.classList.remove("hidden");
      status.textContent = "Corrija o conteúdo para gerar seu QR Code.";
    }
  });
})();
