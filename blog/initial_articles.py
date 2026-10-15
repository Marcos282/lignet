"""Original evergreen editorial guides, not scraped or rewritten news."""

CATEGORIES = {
    "redes": ("Redes e conectividade", "ping,latência,dns,traceroute,http"),
    "enderecamento": ("Endereçamento IP", "ipv4,ipv6,cidr,sub-rede,máscara"),
    "imagens": ("Imagens e desempenho", "imagem,imagens,compressão,webp,jpeg"),
    "produtividade": ("Produtividade digital", "qr code,qrcode"),
    "seo": ("SEO e presença digital", "seo,sitemap,robots,canonical,search console"),
}

# title, category, excerpt, body, reference URLs
ARTICLES = [
    (
        "Como interpretar a latência de um ping sem tirar conclusões precipitadas",
        "redes",
        "Entenda o tempo de ida e volta, compare destinos e use o ping como uma pista de diagnóstico, não como uma sentença sobre sua conexão.",
        """O ping ajuda a observar se um destino responde a mensagens de controle e quanto tempo uma resposta leva para voltar. O valor exibido normalmente representa o tempo de ida e volta, conhecido como RTT. Ele não é uma medida direta da velocidade de download, da qualidade do Wi-Fi ou da experiência de todos os aplicativos.

Para começar, escolha um destino que você tenha autorização para testar. Faça uma sequência curta de medições e registre horário, destino e origem. Uma amostra isolada é pouco informativa: alterações de rota, ocupação dos enlaces e políticas do equipamento remoto podem influenciar a resposta.

Compare primeiro o mesmo destino ao longo do tempo. Comparar um servidor próximo com outro continente mistura fatores diferentes, como distância física e interconexões. Uma latência maior para um destino distante não demonstra, por si só, defeito no provedor.

Também observe a variação entre respostas. Um resultado estável pode se comportar melhor em uma chamada do que valores muito irregulares, mas o ping não reproduz todos os protocolos de uma aplicação. Equipamentos podem limitar ou despriorizar ICMP sem afetar o tráfego principal.

No Ping Mundial da Lignet, as sondas estão em localidades remotas. O resultado descreve o caminho entre a sonda e o alvo, não entre seu celular e o servidor. Use essa diferença a seu favor para comparar perspectivas. Se houver falha, confirme com um teste do serviço real antes de atribuir causa ou responsabilidade.""",
        ["https://www.rfc-editor.org/rfc/rfc792", "https://www.rfc-editor.org/rfc/rfc2681"],
    ),
    (
        "Perda de pacotes: como coletar evidências antes de abrir um chamado",
        "redes",
        "Saiba organizar medições de perda de pacotes e distinguir uma resposta ausente de uma falha comprovada no serviço que você utiliza.",
        """Uma resposta de ping ausente pode indicar perda de pacotes, mas também pode refletir filtragem, limitação de mensagens ou indisponibilidade do destino. O diagnóstico exige contexto. Antes de concluir que a conexão está ruim, registre exatamente qual ferramenta, alvo e origem foram utilizados.

Faça testes curtos em mais de um horário e compare destinos que tenham relação com o problema relatado. Se apenas um serviço apresenta dificuldade, uma falha observada em outro endereço pode não explicar o incidente. Guarde o período da medição e a quantidade de mensagens enviadas, evitando apresentar uma porcentagem sem informar o tamanho da amostra.

Quando possível, compare acesso cabeado e acesso sem fio no mesmo ambiente, com autorização do responsável. Essa comparação reduz algumas variáveis, mas não prova automaticamente que o Wi-Fi é a causa. Equipamentos diferentes, atividades em segundo plano e mudanças de rota ainda podem interferir.

Uma medição com sondas remotas permite investigar se a dificuldade aparece de várias regiões. Ela não substitui testes originados na rede afetada. No relatório, identifique claramente de onde partiram as medições e quais destinos responderam.

Ao abrir um chamado, descreva o sintoma percebido no aplicativo, anexe horários e resultados reproduzíveis e indique o que já foi testado. Evite varreduras prolongadas ou excesso de tráfego. Evidências bem delimitadas ajudam mais do que afirmar que um salto intermediário ou um provedor específico está defeituoso sem confirmação.""",
        ["https://www.rfc-editor.org/rfc/rfc2680", "https://www.rfc-editor.org/rfc/rfc792"],
    ),
    (
        "Traceroute: por que um salto sem resposta não significa uma rota quebrada",
        "redes",
        "Aprenda a ler os saltos de uma rota e entenda por que a ausência de resposta de um roteador intermediário não comprova interrupção.",
        """O traceroute tenta revelar pontos intermediários de um caminho de rede usando pacotes com limites progressivos de saltos. Quando esse limite se esgota, um equipamento pode devolver uma mensagem de controle. A sequência dessas respostas oferece uma visão parcial da rota, não um inventário completo da infraestrutura.

Um asterisco ou um tempo esgotado significa que a ferramenta não recebeu a resposta esperada naquele prazo. O equipamento pode encaminhar o tráfego normalmente e, ao mesmo tempo, limitar mensagens destinadas ao próprio roteador. Se os saltos seguintes respondem, não é correto concluir que o salto silencioso interrompeu a comunicação.

Outro cuidado importante é a assimetria. O caminho de ida pode ser diferente do caminho de volta, e o tempo exibido envolve a resposta retornando à origem. Não subtraia tempos entre saltos como se cada valor medisse apenas um enlace isolado.

Balanceamento de carga e políticas de interconexão também podem alterar os endereços observados entre execuções. Registre horário, tipo de teste e localidade da sonda. Compare medições equivalentes antes de interpretar uma mudança como incidente.

Na ferramenta mundial da Lignet, cada sonda representa uma origem remota. Use os resultados para formular hipóteses e combine-os com testes de DNS e HTTP quando o problema for acesso a um site. Atribuir a falha a uma empresa exige evidências adicionais; o nome reverso de um endereço e um salto lento não bastam para estabelecer responsabilidade.""",
        ["https://www.rfc-editor.org/rfc/rfc1812", "https://www.rfc-editor.org/rfc/rfc792"],
    ),
    (
        "Site não abre: uma sequência prática para verificar DNS e conectividade",
        "redes",
        "Organize o diagnóstico de um site indisponível separando resolução de nomes, conexão, HTTPS e resposta da aplicação.",
        """Quando um site não abre, começar por mudanças aleatórias costuma dificultar a investigação. O acesso depende de etapas diferentes: o nome precisa ser resolvido, a conexão precisa chegar ao destino, o HTTPS precisa ser negociado e a aplicação precisa responder. Uma falha em qualquer etapa pode parecer semelhante para o visitante.

Anote a mensagem exata do navegador e o horário do teste. Confirme se o endereço foi digitado corretamente e se o problema afeta apenas uma página ou o domínio inteiro. Não ignore alertas de certificado nem desative proteções para fazer o site abrir.

Na consulta DNS, verifique se existem endereços públicos para o nome. Registros A se relacionam a IPv4; AAAA, a IPv6. A ausência de um deles não implica necessariamente falha, porque nem todo serviço oferece as duas famílias. Respostas diferentes também podem ser esperadas em serviços distribuídos.

Em seguida, verifique o serviço HTTPS e o status HTTP. Um ping sem resposta não prova que um site está fora do ar: muitos servidores não respondem a ICMP. Da mesma forma, receber uma resposta HTTP de erro comprova que houve comunicação com algum componente, mas não que toda a aplicação esteja saudável.

Compare observações de outras redes ou sondas apenas como evidência complementar. Uma sonda externa não reproduz sua conexão local. Ao registrar o incidente, mantenha separados o que foi observado e as possíveis explicações. Essa disciplina evita alterar DNS, firewall ou configurações de produção sem saber qual etapa realmente falhou.""",
        ["https://www.rfc-editor.org/rfc/rfc1034", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status"],
    ),
    (
        "IPv4 e CIDR: como transformar um endereço em informações de rede",
        "enderecamento",
        "Entenda o prefixo CIDR, a máscara e o intervalo de uma rede IPv4 com um exemplo que pode ser conferido na calculadora da Lignet.",
        """Um endereço IPv4 identifica uma posição em um espaço de 32 bits. Na notação CIDR, o número após a barra informa quantos bits pertencem ao prefixo de rede. Quanto maior esse número, menor é o bloco de endereços representado.

Considere 192.168.10.50/24. O prefixo de 24 bits corresponde à máscara 255.255.255.0. Nesse caso, a rede começa em 192.168.10.0 e termina em 192.168.10.255, reunindo 256 endereços. Em uma sub-rede IPv4 convencional desse tamanho, os extremos têm papéis de rede e broadcast, deixando 254 endereços para hosts.

Não aplique a subtração de dois endereços a todos os prefixos. Redes /31 em enlaces ponto a ponto e endereços /32 têm semânticas próprias. A calculadora deve apresentar essas exceções de forma explícita, em vez de devolver uma quantidade negativa ou tratar todos os casos como uma LAN comum.

Para conferir uma configuração, anote o endereço, o prefixo e o gateway. O fato de dois endereços parecerem próximos na escrita decimal não garante que estejam na mesma sub-rede. A comparação precisa considerar a máscara.

Use a calculadora CIDR da Lignet para confirmar a rede e os limites antes de documentar ou aplicar alterações. O cálculo não verifica se um endereço está livre, se existe uma VLAN correspondente ou se o roteamento foi configurado. Essas etapas dependem do inventário e da administração da rede, e mudanças devem ocorrer com planejamento e possibilidade de reversão.""",
        ["https://www.rfc-editor.org/rfc/rfc4632", "https://www.rfc-editor.org/rfc/rfc3021"],
    ),
    (
        "Redes IPv4 /31 e /32: entenda as exceções na contagem de hosts",
        "enderecamento",
        "Veja por que enlaces ponto a ponto /31 e rotas de host /32 não seguem a mesma regra de contagem usada em uma sub-rede convencional.",
        """A fórmula que retira dois endereços de uma sub-rede IPv4 é uma simplificação útil em muitos cenários, mas não é universal. Aplicá-la mecanicamente aos prefixos /31 e /32 produz interpretações incorretas.

Um bloco /31 contém dois endereços. A RFC 3021 descreve o uso desses dois endereços em enlaces ponto a ponto, sem reservar um endereço de rede e outro de broadcast da forma convencional. Esse uso pressupõe suporte e configuração compatíveis nos equipamentos envolvidos; não transforma automaticamente qualquer segmento compartilhado em um enlace adequado.

Por exemplo, 192.0.2.8/31 abrange 192.0.2.8 e 192.0.2.9. A finalidade do exemplo é explicar o cálculo: o bloco 192.0.2.0/24 é destinado à documentação, não ao endereçamento público de uma rede em produção.

Um prefixo /32 representa um único endereço IPv4. É comum encontrá-lo em rotas de host ou interfaces lógicas, dependendo da plataforma. Não existe ali uma faixa convencional de múltiplos hosts para distribuir. O alcance desse endereço depende das rotas e das demais configurações.

Ao interpretar o resultado de uma calculadora, diferencie o último endereço matemático do bloco de um broadcast utilizável no contexto do enlace. Confira a documentação do equipamento antes de configurar esses prefixos. A calculadora CIDR ajuda a evitar erros aritméticos, mas não substitui a validação do desenho da rede e dos protocolos que operarão sobre ela.""",
        ["https://www.rfc-editor.org/rfc/rfc3021", "https://www.rfc-editor.org/rfc/rfc5737"],
    ),
    (
        "IP privado, IP público e CGNAT: diferenças que afetam o acesso remoto",
        "enderecamento",
        "Diferencie endereços privados, espaço compartilhado de operadoras e endereços públicos antes de investigar acesso remoto ou redirecionamento de portas.",
        """O endereço configurado no seu computador pode ser diferente do endereço observado por um serviço na internet. Essa diferença é comum em redes que usam tradução de endereços, mas não permite concluir, sozinha, como toda a infraestrutura foi organizada.

No IPv4, a RFC 1918 reserva 10.0.0.0/8, 172.16.0.0/12 e 192.168.0.0/16 para uso privado. Esses intervalos não são endereços públicos globais de uma conexão. Eles podem ser reutilizados em redes distintas, desde que o projeto considere possíveis conflitos em VPNs e interligações.

O intervalo 100.64.0.0/10 tem outra finalidade: espaço compartilhado, descrito na RFC 6598 e frequentemente associado a CGNAT. Ele não faz parte dos três blocos privados da RFC 1918. Encontrar um endereço desse intervalo é uma pista, mas o diagnóstico deve considerar a posição da interface e as informações do operador.

Para acesso remoto, o encaminhamento de portas no roteador local pode ser insuficiente quando há outra tradução adiante. Também podem existir filtros de entrada, ausência de rota ou restrições do serviço. Não desative o firewall nem exponha painéis de administração como primeira tentativa.

Registre os endereços observados e consulte o responsável pela conexão. Considere VPNs e soluções de acesso autenticado apropriadas ao caso. A calculadora CIDR da Lignet ajuda a identificar blocos e limites; ela não testa exposição de serviços nem garante que um endereço público aceite conexões de entrada.""",
        ["https://www.rfc-editor.org/rfc/rfc1918", "https://www.rfc-editor.org/rfc/rfc6598"],
    ),
    (
        "IPv6: prefixos e intervalos sem transportar conceitos errados do IPv4",
        "enderecamento",
        "Conheça as diferenças essenciais entre IPv4 e IPv6 ao interpretar prefixos, intervalos de endereços e mecanismos de comunicação local.",
        """IPv6 utiliza endereços de 128 bits. A notação hexadecimal e a compressão de grupos de zeros tornam a escrita mais compacta, mas não alteram a quantidade de bits do endereço. O prefixo após a barra continua indicando quantos bits definem a rede.

Um prefixo /64 deixa 64 bits fora do prefixo e representa um espaço muito grande. Isso não significa que seja útil enumerar todos os endereços em uma tabela. Calculadoras devem trabalhar com limites matemáticos e apresentar os resultados sem produzir listagens gigantes.

Uma diferença importante é a ausência do broadcast do IPv4. IPv6 utiliza outros mecanismos, incluindo multicast, para funções que não devem ser descritas como broadcast IPv4. Também não faz sentido exigir uma máscara decimal pontuada para representar um prefixo IPv6.

Ao copiar endereços, entenda a forma comprimida. A sequência de dois pontos duplos pode substituir um trecho de grupos zero, mas não pode aparecer duas vezes no mesmo endereço. Ferramentas confiáveis devem validar a estrutura, e não apenas contar caracteres.

Use endereços de documentação, como os do bloco 2001:db8::/32, em exemplos públicos. Não confunda o tamanho matemático do bloco com o planejamento real de interfaces, delegação de prefixos e segurança. A calculadora CIDR ajuda a verificar limites; a implantação exige conhecer as orientações da rede, os anúncios de roteador, o DNS e as políticas de firewall para IPv6.""",
        ["https://www.rfc-editor.org/rfc/rfc4291", "https://www.rfc-editor.org/rfc/rfc3849"],
    ),
    (
        "Como planejar sub-redes IPv4 sem sobreposição de endereços",
        "enderecamento",
        "Organize demandas, reserve crescimento e confira limites de blocos antes de dividir uma rede IPv4 em sub-redes menores.",
        """Planejar sub-redes começa pelo levantamento de necessidades, não pela escolha de números que parecem fáceis de lembrar. Documente os segmentos, a quantidade de dispositivos, os endereços de infraestrutura e a expectativa de crescimento.

Em uma LAN IPv4 convencional, a quantidade útil de hosts é menor que o total de endereços do bloco. Verifique as reservas de rede e broadcast e se existem exceções de enlace. Some também gateways, equipamentos de gerenciamento e dispositivos que não aparecem no inventário de estações.

Ao usar blocos de tamanhos diferentes, uma prática de organização é alocar primeiro as maiores demandas, respeitando os limites binários de cada prefixo. Não basta encontrar uma sequência livre na escrita decimal: o início de uma sub-rede precisa ser compatível com sua máscara.

Depois da divisão, confira se os blocos estão inteiramente contidos na rede base e se nenhum intervalo cruza outro. Mantenha uma tabela com finalidade, prefixo, gateway, faixa destinada a DHCP e reservas. Evite publicar inventários internos completos em páginas públicas ou capturas de tela sem necessidade.

A calculadora CIDR pode ajudar a verificar um bloco por vez. Ela não conhece os endereços usados pela sua organização e não deve ser interpretada como prova de que uma faixa está livre. Antes de aplicar mudanças, confira rotas, regras de firewall, VPNs e redes remotas que podem usar intervalos iguais. Uma configuração matematicamente válida ainda pode causar conflito operacional.""",
        ["https://www.rfc-editor.org/rfc/rfc4632", "https://www.rfc-editor.org/rfc/rfc1918"],
    ),
    (
        "TTL e cache DNS: por que uma alteração pode aparecer em momentos diferentes",
        "redes",
        "Entenda como caches e TTL influenciam consultas DNS e por que respostas diferentes não demonstram, sozinhas, um erro de configuração.",
        """O DNS é distribuído e utiliza cache para reduzir consultas repetidas. Um resolvedor pode reutilizar uma resposta enquanto ela ainda estiver válida segundo as regras de cache. Por isso, alterar um registro autoritativo não obriga todos os clientes a consultá-lo novamente no mesmo instante.

O TTL informa um tempo de vida associado ao registro. Ele não é um cronômetro global iniciado quando você clica em salvar no painel do domínio. Resolvedores podem ter recebido a resposta em momentos diferentes, e aplicações ou sistemas operacionais também podem manter seus próprios caches.

Respostas negativas têm regras próprias de armazenamento. Criar um nome que antes não existia pode continuar produzindo uma resposta negativa em um cache por algum tempo. É importante conferir qual servidor respondeu e se o nome consultado está correto.

Para diagnosticar uma mudança, compare o registro no serviço autoritativo e em resolvedores públicos apropriados, registrando tipo, resposta e horário. Não trate toda diferença como defeito: balanceamento geográfico e serviços distribuídos podem fornecer endereços diferentes intencionalmente.

Evite prometer um prazo universal de propagação. Planeje mudanças com antecedência, consulte o TTL existente e entenda as regras do provedor DNS. A consulta DNS da Lignet oferece uma visão do ambiente de consulta utilizado; medições em outras localidades acrescentam perspectivas, mas nenhuma consulta isolada demonstra o estado de todos os caches da internet.""",
        ["https://www.rfc-editor.org/rfc/rfc1034", "https://www.rfc-editor.org/rfc/rfc2308"],
    ),
    (
        "Erros HTTP 404, 502 e 500: como separar rota, proxy e aplicação",
        "redes",
        "Use o status HTTP como ponto de partida para localizar falhas entre o servidor web, o proxy reverso e a aplicação, sem esconder os erros.",
        """Um status HTTP descreve a resposta de um componente que recebeu a requisição. Ele ajuda a orientar o diagnóstico, mas não revela sozinho toda a cadeia de serviços. Em uma instalação com Nginx e Django, a resposta pode vir do servidor web, de um proxy ou da aplicação.

Um 404 indica que o recurso solicitado não foi encontrado por quem respondeu. Se o Nginx procura um arquivo estático para uma rota que deveria chegar ao Django, criar outra página não corrige a regra de encaminhamento. Primeiro confira a URL e a configuração efetivamente carregada.

Um 502 costuma apontar dificuldade do intermediário em obter uma resposta válida do upstream. Verifique se o processo correto está ativo e se a porta ou o socket correspondem à configuração. Uma porta ocupada não significa que ela pertence à aplicação esperada; identifique o processo antes de reiniciar qualquer serviço.

Um 500 indica falha interna no tratamento da requisição. O passo seguinte é consultar o log da aplicação ou reproduzir a operação em um ambiente controlado. Não exponha páginas de depuração em produção nem publique credenciais ao compartilhar um traceback.

Valide a configuração do servidor antes de recarregar e preserve uma possibilidade de retorno. Depois de a página abrir, confira também CSS, JavaScript e os endpoints de processamento. Uma página com status 200 não comprova que filas, banco de dados e tarefas em segundo plano estejam saudáveis. O teste HTTP mundial pode complementar a observação externa, sem substituir logs locais.""",
        ["https://developer.mozilla.org/en-US/docs/Web/HTTP/Status"],
    ),
    (
        "Como reduzir uma imagem preservando a qualidade que realmente importa",
        "imagens",
        "Combine dimensões, formato e qualidade para produzir imagens menores, sempre comparando o arquivo exportado com o original.",
        """Reduzir uma imagem não é apenas diminuir um controle de qualidade. O tamanho final depende das dimensões, do conteúdo visual, do formato e do nível de compressão. Uma fotografia e uma captura de tela podem reagir de maneiras diferentes à mesma configuração.

Comece pela dimensão de exibição. Se a página não precisa de uma imagem enorme, exportar uma versão com menos pixels pode economizar espaço sem prejudicar a apresentação desejada. Preserve uma cópia original e evite ampliar uma imagem pequena na expectativa de recuperar detalhes que não existem.

Depois compare formatos adequados ao conteúdo. Fotografias geralmente toleram compressão com perdas, enquanto gráficos com texto fino e áreas chapadas podem exigir mais cuidado. O resultado precisa ser observado na escala de uso, especialmente em bordas, letras e detalhes de alto contraste.

No redutor da Lignet, a imagem é processada no navegador. Escolha a largura máxima, o formato e, quando aplicável, a qualidade. Baixe a cópia e compare os bytes e a aparência. Converter para outro formato não garante redução: em alguns casos o novo arquivo pode ficar maior.

Transparência também importa. Ao exportar para JPEG, uma área transparente precisa receber um fundo, porque esse formato não preserva um canal alfa. Evite recomprimir repetidamente versões já comprimidas e mantenha um arquivo mestre para novas exportações. O melhor ajuste é o que atende ao uso real com qualidade visual suficiente, não necessariamente o menor arquivo possível.""",
        ["https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Image_types"],
    ),
    (
        "JPEG, PNG ou WebP: como escolher o formato de uma imagem para a web",
        "imagens",
        "Compare características de JPEG, PNG e WebP e escolha um formato considerando conteúdo visual, transparência e compatibilidade.",
        """Não existe um formato de imagem universalmente melhor para todas as situações. A escolha depende da imagem, da qualidade necessária e dos programas que vão abrir o arquivo. Comparar versões reais é mais confiável do que assumir uma economia fixa.

JPEG é amplamente usado para fotografias e trabalha com compressão com perdas. Ao reduzir a qualidade, detalhes podem se degradar, especialmente após exportações sucessivas. O formato não preserva transparência, o que exige atenção em logos e elementos recortados.

PNG utiliza compressão sem perdas e suporta transparência. Pode ser adequado para gráficos, interfaces e imagens em que a preservação exata dos pixels importa. Isso não significa que sempre será pequeno: fotografias em PNG podem consumir bastante espaço.

WebP oferece modos com e sem perdas e suporte a transparência. Ele pode ser uma boa opção para publicação web, mas a decisão deve considerar o fluxo de edição, os aplicativos de destino e o resultado obtido. Evite afirmar que a conversão sempre reduzirá o arquivo.

Para escolher, gere algumas alternativas com a mesma dimensão e examine detalhes relevantes na escala de exibição. Confira transparência, cores, nitidez do texto e tamanho final. O redutor da Lignet facilita essa comparação localmente. Guarde o original, descreva a imagem com um texto alternativo apropriado na página e não dependa apenas da extensão do arquivo para avaliar a qualidade ou o tipo do conteúdo.""",
        ["https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Image_types"],
    ),
    (
        "Fotos em artigos: texto alternativo, créditos e contexto para o leitor",
        "imagens",
        "Publique fotos próprias com descrição acessível e créditos, sem apresentar uma imagem ilustrativa como prova de um acontecimento.",
        """Uma foto pode tornar um artigo mais claro e acolhedor, mas precisa cumprir um papel editorial. Escolher uma imagem apenas para preencher espaço pode confundir o leitor, especialmente quando ela parece registrar um acontecimento que não está documentado.

Prefira fotos próprias ou material com permissão de publicação comprovada. Registre o autor e as condições de uso. Encontrar uma imagem em um buscador ou em uma notícia não transfere o direito de republicá-la. Pessoas identificáveis e informações em telas também exigem atenção.

O texto alternativo deve comunicar a informação visual relevante no contexto da página. Ele não deve ser uma lista de palavras-chave nem repetir o título sem necessidade. Para uma foto ilustrativa de equipamentos, descreva o que ajuda a compreender o conteúdo, sem inventar modelo, local ou situação.

Legenda e crédito têm funções distintas. A legenda pode esclarecer que a imagem é ilustrativa; o crédito identifica a autoria. Uma foto genérica de um roteador não demonstra que aquele equipamento participou de uma falha de conectividade.

Antes de publicar, remova informações sensíveis da imagem e confira se metadados podem revelar localização ou outros detalhes desnecessários. Dimensione o arquivo para o uso na página, use o redutor de imagens quando adequado e revise a descrição com a mesma atenção dedicada ao texto. Acessibilidade e precisão editorial beneficiam o leitor; não são uma promessa automática de posicionamento no Google.""",
        ["https://www.w3.org/WAI/tutorials/images/", "https://developers.google.com/search/docs/appearance/google-images"],
    ),
    (
        "QR Code para links: como gerar e conferir o destino com segurança",
        "produtividade",
        "Crie QR Codes para endereços web, teste o arquivo gerado e ajude o leitor a reconhecer o destino antes de abrir um link.",
        """Um QR Code pode armazenar um endereço web ou outro conteúdo textual. Ao ler o código, o aplicativo interpreta os dados e pode oferecer uma ação, como abrir um site. O código não comprova que o destino é legítimo, seguro ou administrado por quem o imprimiu.

Para criar um código de link, use o endereço completo com https:// e confira cada caractere. Um erro no domínio pode enviar o usuário para um site diferente. Evite inserir tokens, senhas ou links privados: quem tiver acesso à imagem também poderá ler o conteúdo.

Depois de gerar, baixe o PNG e teste o próprio arquivo exportado, não apenas a prévia. Use a câmera de um celular ou outro leitor confiável e compare o endereço reconhecido com o endereço pretendido. O gerador da Lignet processa o conteúdo localmente e não precisa enviar o texto para um serviço de criação de códigos.

Ao publicar, inclua uma indicação legível do destino e uma alternativa em link de texto quando possível. Isso melhora a compreensão e atende pessoas que não podem usar uma câmera naquele momento. Não esconda o endereço atrás de promessas vagas.

Lembre-se de que um código estático não atualiza seu conteúdo depois de impresso. Se o endereço mudar, o código antigo continua representando o texto original. Planeje uma URL estável e mantenha o destino sob controle. Não confunda funcionamento da leitura com garantia de segurança do site acessado.""",
        ["https://www.qrcode.com/en/about/"],
    ),
    (
        "QR Code na impressão: margem branca, contraste e teste em tamanho real",
        "produtividade",
        "Prepare um QR Code para materiais impressos sem cortar a margem de leitura e confira o resultado nas condições reais de uso.",
        """Um QR Code legível depende de mais do que sua aparência em uma tela grande. A impressão, o papel, o contraste, a iluminação e a distância de leitura influenciam o resultado. Antes de produzir um lote, teste uma amostra nas condições em que o público vai utilizá-la.

Preserve a área branca ao redor do código. Essa margem ajuda o leitor a separar os módulos do restante do layout. Para QR Code convencional, a orientação de margem é de pelo menos quatro módulos em cada lado. Cortar a imagem rente aos quadrados pode prejudicar a detecção.

Use bom contraste e evite texturas ou fotografias sob os módulos. Preto sobre branco é uma escolha simples e previsível. Não coloque logos sobre o código nem distorça suas proporções sem avaliar o impacto com leitores independentes.

O volume de texto altera a densidade do símbolo. Um endereço muito longo pode exigir mais módulos e dificultar a leitura em áreas pequenas. Prefira uma URL estável e curta que você controle, sem depender desnecessariamente de encurtadores desconhecidos.

Exporte o arquivo, insira no layout e imprima no tamanho final. Teste com diferentes aparelhos e ângulos, sem assumir que uma leitura bem-sucedida na tela garante a impressão. A ferramenta da Lignet oferece PNG em dois tamanhos; o número de pixels não define sozinho o tamanho físico apropriado. Preserve a margem ao redimensionar e disponibilize também um endereço legível para quem não conseguir usar o código.""",
        ["https://www.qrcode.com/en/howto/code.html", "https://www.qrcode.com/en/about/"],
    ),
    (
        "Sitemap XML: como apresentar ao Google as páginas públicas do seu site",
        "seo",
        "Entenda o papel do sitemap XML, inclua apenas URLs públicas e acompanhe o processamento sem tratar o envio como garantia de indexação.",
        """Um sitemap XML informa aos mecanismos de busca quais URLs você deseja apresentar para descoberta e rastreamento. Ele é especialmente útil quando o site cresce ou tem páginas difíceis de encontrar pela navegação, mas não substitui links internos e não obriga um buscador a indexar conteúdo.

Inclua endereços absolutos, estáveis e compatíveis com as URLs canônicas. Evite rascunhos, históricos privados, páginas administrativas e links que dependem de sessão. Listar uma página restrita não a torna pública; apenas cria uma indicação inadequada para o robô.

A informação de última modificação deve refletir uma mudança significativa real. Alterar datas automaticamente sem mudar o conteúdo pode reduzir a utilidade do dado. Em sites grandes, use divisão em sitemaps e um índice, respeitando os limites do protocolo.

No blog da Lignet, apenas artigos publicados e já disponíveis entram no sitemap. Agendamentos futuros e artigos retirados manualmente ficam de fora. A paginação do sitemap permite crescer sem montar um único documento enorme.

Depois de publicar o arquivo, confira se ele responde corretamente e se as URLs funcionam para visitantes sem login. O Google Search Console pode receber o endereço do sitemap e mostrar informações sobre seu processamento. O envio não garante tráfego, indexação ou posição. Conteúdo útil, acesso consistente e uma estrutura interna clara continuam sendo parte essencial do trabalho.""",
        ["https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview", "https://www.sitemaps.org/protocol.html"],
    ),
    (
        "Robots.txt e noindex: controles diferentes para objetivos diferentes",
        "seo",
        "Diferencie regras de rastreamento e diretivas de indexação e evite usar robots.txt como proteção para conteúdo privado.",
        """O arquivo robots.txt oferece instruções de rastreamento para robôs que seguem o protocolo. Ele não funciona como autenticação e não impede que uma pessoa acesse uma URL conhecida. Informações privadas precisam de controles de acesso no servidor.

Uma regra Disallow pode impedir que um robô compatível busque o conteúdo de um caminho. Isso não equivale necessariamente a remover o endereço dos resultados de busca. Um mecanismo pode conhecer a URL por outros links, mesmo sem poder ler a página.

A diretiva noindex tem outro objetivo: indicar que o conteúdo não deve ser indexado pelos mecanismos que a respeitam. Para que uma diretiva na página seja lida, o robô precisa conseguir acessar essa resposta. Bloquear o rastreamento e esperar que ele descubra uma metatag nova pode produzir um resultado diferente do desejado.

Use cabeçalhos ou metatags adequados ao tipo de recurso e valide a resposta real. Páginas de conta, relatórios privados e painéis administrativos devem depender principalmente de autenticação e autorização. Não coloque segredos em caminhos que você espera esconder apenas com regras de robô.

Ao revisar uma configuração, separe os objetivos: limitar rastreamento, evitar indexação e restringir acesso são tarefas distintas. A ferramenta de robots.txt da Lignet ajuda a montar o arquivo, mas não decide quais regras são corretas para o seu negócio. Teste mudanças cuidadosamente e acompanhe o comportamento com as ferramentas do buscador, sem esperar remoção imediata.""",
        ["https://developers.google.com/search/docs/crawling-indexing/robots/intro", "https://developers.google.com/search/docs/crawling-indexing/block-indexing"],
    ),
    (
        "URL canônica: como manter sinais consistentes entre versões de uma página",
        "seo",
        "Organize links internos, sitemap e canonical para indicar a versão preferida de um conteúdo, sem esconder páginas realmente diferentes.",
        """Um mesmo conteúdo pode ficar acessível por vários endereços, por exemplo quando existem parâmetros de navegação ou versões alternativas. A indicação canônica ajuda a comunicar qual URL você prefere para representar esse conjunto de páginas equivalentes.

O elemento rel=canonical é um sinal, não uma ordem absoluta para o buscador. Ele funciona melhor quando está alinhado com redirecionamentos adequados, links internos, sitemap e o conteúdo efetivamente disponível. Sinais contraditórios tornam a interpretação mais difícil.

Use endereços absolutos e confira se a URL indicada responde corretamente. Não aponte todos os artigos de um blog para a página inicial: textos diferentes não são duplicatas da home. Também não use canonical como substituto para restringir acesso a informações privadas.

Na paginação, cada página de listagem pode apresentar um conjunto próprio de artigos. A URL canônica precisa refletir essa diferença quando as páginas não são equivalentes. O leitor e o robô devem conseguir navegar para os próximos conjuntos por links reais.

Ao revisar uma publicação, compare a URL visível, a canonical, os links do sitemap e os links internos. Verifique se há versões HTTP e HTTPS ou domínios alternativos que precisam de redirecionamento. O analisador SEO da Lignet pode apontar sinais a investigar, mas a decisão sobre equivalência exige conhecer o conteúdo. Consistência técnica ajuda a organização do site; não garante que o Google selecione a versão indicada nem que uma página alcance uma posição específica.""",
        ["https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls"],
    ),
    (
        "Google Search Console: o que acompanhar depois de publicar um artigo",
        "seo",
        "Acompanhe descoberta, indexação e desempenho de artigos com expectativas realistas e sem confundir envio de sitemap com aprovação editorial.",
        """Publicar um artigo e enviar um sitemap são etapas de disponibilização, não uma garantia de presença na busca. O Google Search Console oferece informações sobre propriedades autorizadas e ajuda a investigar como o buscador está encontrando e tratando páginas do site.

Comece verificando a propriedade correta. Um domínio e um prefixo de URL podem representar escopos diferentes. Confirme que a conta conectada tem a permissão necessária e não compartilhe tokens ou credenciais para obter ajuda com a configuração.

Confira o processamento do sitemap e use a inspeção de URL quando houver dúvida sobre uma página específica. Separe a versão conhecida pelo Google de um eventual teste ao vivo: são observações com finalidades diferentes. Alterações no site não precisam aparecer imediatamente nos relatórios.

Nos relatórios de desempenho, observe o período, os filtros e as definições de cada métrica. Impressões não equivalem a visitas, e uma variação curta não comprova que uma mudança editorial causou crescimento ou queda. Evite publicar capturas com informações privadas sem autorização.

No painel da Lignet, a integração existente pode atualizar dados da propriedade verificada e enviar um sitemap. Esse envio informa um endereço ao serviço; ele não aprova o texto, não verifica automaticamente cada afirmação e não promete ranking. Use os sinais para priorizar melhorias úteis ao leitor: clareza, referências, navegação entre artigos relacionados e ferramentas que realmente resolvam o problema apresentado.""",
        ["https://support.google.com/webmasters/answer/9128668", "https://developers.google.com/search/docs/fundamentals/creating-helpful-content"],
    ),
]
