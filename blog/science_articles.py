"""Original educational articles; no fictional discoveries or copied source text."""

CATEGORIES = {
    "astronomia": ("Astronomia", "astronomia,estrela,estrelas,planeta,planetas,exoplaneta,telescópio,universo"),
    "utopia": ("Utopia e futuros possíveis", "utopia,cidade,futuro,tecnologia,sociedade,automação"),
    "inteligencia-artificial": ("Inteligência artificial", "inteligência artificial,modelo,modelos,llm,ollama,aprendizado"),
}

# title, category, excerpt, original body, references, image prompt
ARTICLES = [
    (
        "Olhar para o céu é olhar para o passado? Entenda o tempo da luz",
        "astronomia",
        "A luz leva tempo para viajar. Entenda como essa ideia ajuda a interpretar observações do céu sem confundir distância com idade.",
        """Quando vemos um objeto, recebemos luz que saiu dele ou foi refletida por ele anteriormente. Em situações cotidianas, esse atraso costuma ser pequeno demais para nossa percepção. Em astronomia, as distâncias tornam o tempo de viagem da luz parte essencial da interpretação.

Isso significa que observar uma estrela é receber informação sobre um estado anterior dela. Não significa que possamos escolher livremente qualquer momento de sua história. O telescópio registra a luz que está chegando ao instrumento naquela observação, com limites de sensibilidade, resolução e duração da exposição.

O ano-luz é uma unidade de distância, não uma medida da idade de uma estrela. Ele corresponde à distância percorrida pela luz no vácuo durante um ano. Dizer que algo está a muitos anos-luz não informa sozinho quando esse objeto se formou ou como evoluiu.

Em escalas cosmológicas, a expansão do universo exige ainda mais cuidado. Distância atual, distância percorrida pela luz e tempo desde a emissão não são sempre maneiras equivalentes de expressar a mesma coisa. São conceitos diferentes dentro de um modelo cosmológico.

Para ler uma notícia sobre um objeto distante, procure o significado da distância citada, o instrumento utilizado e o que foi efetivamente medido. Uma imagem pode combinar diferentes exposições e faixas de luz; não deve ser entendida automaticamente como uma fotografia de cores naturais.

O valor dessa perspectiva é reconhecer que o céu contém informação histórica. Ela permite estudar evolução estelar e cósmica, mas não elimina as incertezas das observações. Uma ilustração de galáxias pode ajudar a explicar o assunto; não é um registro científico nem prova de uma descoberta.""",
        ["https://science.nasa.gov/universe/"],
        "Educational astronomy illustration of starlight traveling across a deep blue universe, layered stars and distant galaxies, elegant editorial art, not a telescope photograph, no text or labels.",
    ),
    (
        "Como procurar exoplanetas sem fotografar diretamente cada planeta",
        "astronomia",
        "Conheça trânsito e velocidade radial, dois métodos de pesquisa de exoplanetas, e entenda por que cada medição exige interpretação.",
        """Um exoplaneta é um planeta que orbita uma estrela fora do Sistema Solar. Encontrar esses mundos não exige, em todos os casos, obter uma imagem em que apareçam separados da estrela. Muitas pesquisas investigam efeitos indiretos associados à presença de um companheiro orbital.

No método do trânsito, acompanha-se o brilho de uma estrela. Quando a geometria permite, um planeta passa à frente dela em relação ao observador e bloqueia uma pequena parcela da luz. A repetição e o formato dessa variação oferecem pistas, mas uma queda de brilho isolada não confirma automaticamente um planeta.

Estrelas variáveis, sistemas estelares múltiplos e problemas instrumentais podem produzir sinais que precisam ser distinguidos. Pesquisadores usam observações adicionais, análise estatística e verificações de consistência. Nem todo sistema planetário é orientado de modo a produzir trânsitos vistos da Terra.

Na velocidade radial, procura-se o movimento da estrela na direção do observador e na direção oposta, percebido por alterações em seu espectro. O fenômeno permite inferir propriedades do sistema, com limitações ligadas à inclinação orbital e à atividade da própria estrela.

Os métodos respondem a perguntas distintas e podem se complementar. Estimar tamanho, massa e características orbitais exige indicar quais dados estão disponíveis e quais hipóteses foram usadas. Não se deve transformar automaticamente uma estimativa de tamanho em uma descrição da superfície.

Ao encontrar uma imagem de exoplaneta, confira se é observação direta ou concepção artística. Uma ilustração é útil para comunicação, mas não revela cores, oceanos ou habitantes desconhecidos. A presença de um planeta também não equivale a evidência de vida.""",
        ["https://science.nasa.gov/exoplanets/"],
        "Conceptual educational illustration of a small planet crossing in front of a distant star, dark blue space, restrained warm stellar light, clear artistic rendering, no life claims, no text.",
    ),
    (
        "Buracos negros: o que observar não significa ver por dentro",
        "astronomia",
        "Diferencie horizonte de eventos, material ao redor e sinais observados para compreender imagens e explicações sobre buracos negros.",
        """A expressão buraco negro descreve uma região do espaço-tempo da qual a luz não consegue escapar para observadores distantes depois de cruzar o horizonte de eventos. Essa definição não implica que tudo ao redor seja invisível ou que um telescópio revele seu interior.

Matéria aquecida nas proximidades pode emitir radiação. A interação entre gravidade, gás, campos magnéticos e movimento produz fenômenos que os instrumentos observam em diferentes faixas. Alguns sistemas também apresentam jatos; não é correto dizer que eles são matéria saindo de dentro do horizonte.

Uma imagem associada à sombra de um buraco negro envolve emissão do ambiente e os efeitos gravitacionais sobre a luz. Interpretá-la exige modelos, calibração e comparação com os dados. Não é uma fotografia de uma superfície sólida nem um retrato de uma singularidade.

Também podemos estudar esses objetos por movimentos de estrelas, emissão de sistemas binários e ondas gravitacionais. Cada abordagem informa aspectos diferentes. A conclusão científica resulta da combinação entre observações e teorias que podem ser confrontadas com evidências.

Ideias sobre viagens por buracos negros e atalhos cósmicos aparecem na ficção. Não devem ser apresentadas como tecnologias disponíveis nem como demonstrações de que seres humanos conseguiriam atravessá-los com segurança. Hipóteses matemáticas e possibilidades físicas verificadas são categorias distintas.

Ao compartilhar uma ilustração, mantenha essa distinção explícita. Uma representação artística pode tornar a discussão mais acessível, mas não fornece detalhes observacionais adicionais. Prefira explicações que indiquem o que foi medido, o que foi inferido e onde permanecem perguntas abertas.""",
        ["https://science.nasa.gov/universe/black-holes/"],
        "Editorial scientific concept art of a black hole surrounded by a luminous accretion disk, subtle gravitational lensing, dark navy background, clearly artistic not observational evidence, no text.",
    ),
    (
        "Começar na astronomia sem comprar um telescópio",
        "astronomia",
        "Organize observações do céu a olho nu, registre condições e aprenda a reconhecer limites antes de investir em equipamentos.",
        """Observar o céu pode começar com curiosidade, paciência e um registro simples. Não é preciso comprar um telescópio para perceber mudanças na Lua, identificar padrões aparentes de estrelas e acompanhar como a visibilidade varia ao longo do tempo.

Escolha um local seguro e permitido, afastado de obstáculos e de iluminação direta quando possível. Registre data, horário aproximado, direção observada e condições de nuvens. Poluição luminosa, transparência atmosférica e obstáculos do horizonte afetam o que pode ser visto.

Um mapa celeste configurado para sua localização e horário pode orientar a observação. Ele é uma referência de planejamento, não uma garantia de visibilidade. Não compartilhe publicamente sua localização exata se isso expuser sua residência ou rotina.

Faça anotações antes de confiar na memória. Uma luz em movimento não deve ser classificada imediatamente como objeto astronômico incomum: aeronaves, satélites e fenômenos locais precisam ser considerados. A observação responsável separa descrição do que foi visto e interpretação do que poderia ser.

Nunca olhe diretamente para o Sol por binóculos, telescópios ou dispositivos improvisados. Isso pode causar lesões permanentes. Observação solar exige equipamentos específicos e orientação competente; óculos escuros comuns não tornam essa prática segura.

Depois de algumas sessões, você terá perguntas mais claras sobre o tipo de instrumento que faria sentido adquirir. Clubes de astronomia, planetários e atividades educativas podem oferecer contato com diferentes equipamentos. O objetivo inicial é aprender a observar e reconhecer limites, não produzir descobertas a partir de uma fotografia pouco definida.""",
        ["https://science.nasa.gov/skywatching/"],
        "Peaceful editorial illustration of a person observing a starry night from a safe public observation area, moon and subtle stars, no telescope pointed at sun, no text, artistic scene.",
    ),
    (
        "Utopia não é previsão: como imaginar futuros sem vendê-los como certeza",
        "utopia",
        "Use cenários utópicos como ferramentas de reflexão sobre valores e escolhas, mantendo clara a diferença entre imaginação e evidência.",
        """Imaginar uma sociedade melhor pode ajudar a questionar problemas do presente. Uma utopia, porém, não deve ser confundida com uma previsão científica de que determinado futuro ocorrerá. Ela pode funcionar como exercício filosófico, narrativa ou instrumento de crítica.

Um cenário começa com escolhas: o que conta como vida boa, quem participa das decisões e quais conflitos são considerados aceitáveis? Responder a essas perguntas torna visíveis os valores envolvidos. Uma imagem de cidade limpa e tecnológica não demonstra que seus habitantes tenham liberdade, inclusão ou qualidade de vida.

Para explorar um futuro possível, explicite as premissas. Se o cenário pressupõe energia abundante, instituições confiáveis ou distribuição justa de recursos, examine o que precisaria mudar para isso acontecer. Não transforme essas condições em fatos já alcançados.

Também pergunte quem poderia ser prejudicado. Soluções apresentadas como universais podem ignorar diferenças culturais, desigualdade de acesso e formas legítimas de discordância. A ausência de conflito em uma narrativa pode representar uma simplificação, e não uma sociedade desejável.

Comparar cenários é mais produtivo do que aceitar um desenho único como inevitável. Um mesmo recurso técnico pode ser empregado de maneiras diferentes conforme regras, interesses e instituições. Tecnologia não determina sozinha a organização social.

Este texto propõe reflexão, não uma promessa política ou previsão. Ilustrações de futuros urbanos são conceituais: não retratam projetos aprovados ou lugares existentes. Seu valor está em abrir perguntas e tornar alternativas discutíveis, sem substituir debate público por uma visão sedutora de progresso automático.""",
        ["https://plato.stanford.edu/entries/thomas-more/"],
        "Conceptual utopian city illustration with accessible public gardens and shared spaces, varied human scale buildings, speculative artistic scenario not a real city project, no logos or text.",
    ),
    (
        "Uma cidade inteligente é necessariamente uma cidade melhor?",
        "utopia",
        "Sensores e automação podem apoiar serviços urbanos, mas um futuro desejável também depende de governança, privacidade e acesso.",
        """Chamar uma cidade de inteligente costuma destacar recursos digitais, sensores e sistemas de análise. Essa linguagem pode chamar atenção para oportunidades, mas não demonstra que a vida da população melhorou. Avaliar um serviço exige definir o problema, os beneficiários e os efeitos observados.

Em um cenário hipotético, sensores poderiam apoiar manutenção de iluminação e planejamento de mobilidade. Para avaliar a proposta, seria preciso comparar custos, qualidade do serviço e alternativas menos complexas. Instalar dispositivos não deve ser tratado como resultado final.

Dados sobre deslocamento e comportamento também envolvem privacidade. Quem coleta, por quanto tempo guarda e com quem compartilha? Um serviço público não se torna justo apenas porque um algoritmo participa das decisões. Transparência e meios de contestação continuam importantes.

Pense também em quem não possui celular recente ou acesso constante à internet. Se um serviço essencial funciona apenas por aplicativo, a inovação pode criar uma barreira adicional. Projetar canais acessíveis e alternativas presenciais faz parte do problema, não é um detalhe posterior.

A dependência de fornecedores e a continuidade operacional merecem atenção. O que acontece se uma licença vence, a empresa encerra atividades ou a conexão cai? Interoperabilidade, documentação e capacidade de operação local podem reduzir riscos, mas exigem manutenção.

Como reflexão utópica, uma cidade conectada pode inspirar escolhas. Como afirmação sobre um projeto real, ela precisa de evidências verificáveis. A ilustração que acompanha este artigo é conceitual e não demonstra que uma cidade ou política específica alcançou os benefícios imaginados.""",
        ["https://unhabitat.org/programme/people-centered-smart-cities"],
        "Speculative inclusive city concept with public transport, trees and accessible pedestrian areas, subtle technology integrated into human scale spaces, editorial illustration, no surveillance closeups, no text.",
    ),
    (
        "Automação e tempo livre: uma pergunta social, não só tecnológica",
        "utopia",
        "Imagine cenários de automação distinguindo capacidades técnicas de escolhas sobre trabalho, renda, cuidado e distribuição de benefícios.",
        """A ideia de máquinas liberarem tempo humano aparece em muitas visões de futuro. Mas reduzir o tempo gasto em uma tarefa não determina automaticamente como o benefício será distribuído. Essa passagem envolve decisões econômicas, relações de trabalho e instituições.

Em um cenário hipotético, uma organização poderia automatizar uma atividade repetitiva e diminuir a jornada. Outra poderia usar a mesma capacidade para ampliar a produção sem alterar o tempo de trabalho. Não é a ferramenta, isoladamente, que escolhe entre essas alternativas.

Também é necessário considerar o trabalho que não aparece na demonstração tecnológica. Sistemas precisam ser mantidos, dados exigem cuidado e resultados precisam ser avaliados. A promessa de operação sem pessoas frequentemente deixa de fora essas tarefas e seus custos.

Perguntas sobre tempo livre incluem trabalho de cuidado, acessibilidade e oportunidades de participação cultural. Uma sociedade pode ser produtiva e ainda distribuir de modo desigual descanso e autonomia. Por isso, indicadores de eficiência não são equivalentes a bem-estar.

Um exercício útil é escrever dois cenários com a mesma tecnologia e regras diferentes. Compare quem decide, quem recebe os benefícios, quem assume os riscos e quais mecanismos de revisão existem. Essa comparação torna explícitas as escolhas escondidas em uma promessa de futuro inevitável.

O objetivo deste artigo é oferecer um roteiro de reflexão, não prever o fim do trabalho nem recomendar uma política como conclusão comprovada. A ilustração é uma representação imaginada. Qualquer afirmação sobre efeitos concretos de automação em uma comunidade exige fontes, período de análise e atenção às condições locais.""",
        ["https://www.ilo.org/topics/future-work"],
        "Thoughtful editorial illustration of people sharing learning and creative activities with helpful abstract machines in background, speculative balanced future, no real company or claims, no text.",
    ),
    (
        "Modelos de linguagem: respostas convincentes não são garantia de verdade",
        "inteligencia-artificial",
        "Entenda por que um modelo de linguagem pode escrever com fluidez e ainda errar fatos, referências e conclusões importantes.",
        """Um modelo de linguagem produz sequências de texto a partir de padrões aprendidos e do contexto recebido. Essa capacidade permite resumir, explicar e redigir, mas não transforma cada resposta em uma consulta a uma base de fatos atualizada e verificada.

Uma frase pode soar segura e estar errada. O modelo pode combinar elementos de maneiras plausíveis, inventar uma referência ou responder com informação inadequada ao contexto. Fluidez, extensão e tom de autoridade não são métodos de validação.

Para usar uma resposta em um artigo, separe as afirmações que precisam de comprovação. Confira nomes, datas, números e fontes originais. Abrir o link é importante: a existência de uma URL não garante que ela contenha a afirmação atribuída a ela.

O contexto enviado também importa. Textos externos podem conter instruções que tentam alterar o comportamento do sistema. Limitar permissões, tratar esse material como dados e não disponibilizar ferramentas desnecessárias reduz riscos, sem garantir proteção absoluta.

Execução local modifica onde o processamento acontece, não a confiabilidade intrínseca do texto. Um modelo rodando no seu servidor ainda pode errar. Ele também exige memória, atualização e monitoramento de tempo de execução.

No blog, identificar o auxílio de IA ajuda o leitor a compreender o processo de produção. Uma automação pode validar formato, detectar alguns trechos repetidos e conferir se há referências, mas essas verificações não equivalem a revisão factual. Para decisões com consequências importantes, procure fontes competentes e não use apenas a resposta do modelo como fundamento.""",
        ["https://www.nist.gov/itl/ai-risk-management-framework"],
        "Editorial conceptual illustration of a language model represented by abstract connected shapes beside a human reviewing documents, calm blue tones, emphasis on verification not a thinking human robot, no text.",
    ),
    (
        "IA local e Cron: como separar geração de conteúdo e publicação",
        "inteligencia-artificial",
        "Um agendador deve continuar cuidando dos artigos prontos mesmo quando o modelo local está desligado ou indisponível.",
        """Gerar um texto e publicar um texto pronto são operações diferentes. Essa separação é importante para que uma falha no modelo não paralise toda a rotina editorial. O agendador deve consultar o estado de cada etapa, em vez de pressupor que todas terão sucesso.

O Cron inicia um comando em horários definidos. Ele não é um modelo de inteligência artificial e não depende da assinatura de um assistente de programação. Uma assinatura encerrada não desliga, por si só, serviços já instalados em um servidor sob sua administração.

No processamento local, modelos e arquivos precisam estar disponíveis no equipamento. Ainda existem custos de hospedagem, energia, armazenamento e manutenção. Se o próprio servidor deixar de funcionar ou sua hospedagem for suspensa, não há como garantir continuidade apenas pela escolha de software.

Uma rotina robusta publica primeiro o material aprovado cujo horário já chegou. Depois pode tentar coletar pautas e gerar conteúdo novo. Falhas de conexão com o modelo são registradas e não devem ser disfarçadas como artigos concluídos.

Imagens podem exigir uma fila própria. Em vez de aguardar indefinidamente uma GPU, o comando registra um identificador e consulta a conclusão em outra execução. O artigo permanece pendente até que a capa válida esteja disponível. Reenviar trabalhos caros a cada tentativa pode sobrecarregar o servidor.

A configuração também deve distinguir pausar geração e pausar publicação. Assim, o operador consegue desligar um modelo para manutenção mantendo a distribuição do estoque pronto. Esse desenho não elimina a necessidade de monitorar logs, espaço em disco e a existência real do Cron.""",
        ["https://docs.ollama.com/api", "https://man7.org/linux/man-pages/man5/crontab.5.html"],
        "Editorial illustration of two independent workflow paths, one abstract local computer generating content and another calendar distributing completed documents, no text, no logos, clean navy and green design.",
    ),
    (
        "Imagens geradas por IA: ilustração não é evidência de um acontecimento",
        "inteligencia-artificial",
        "Use imagens sintéticas com identificação clara, contexto e licença conferida, especialmente em temas científicos e cenários de futuro.",
        """Uma imagem gerada por inteligência artificial pode tornar um tema abstrato mais acessível. Ela não prova que o objeto retratado existe, que um evento ocorreu ou que uma hipótese científica foi confirmada. Essa diferença deve estar clara antes de a imagem ser publicada.

Em astronomia, uma representação pode sugerir a aparência de um planeta ou ilustrar um conceito. Ela não deve ser apresentada como captura de um telescópio. Cores, atmosfera e paisagem podem ser escolhas artísticas sem correspondência em dados observacionais.

Em cenários utópicos, uma cidade imaginada não é um projeto aprovado nem um registro de benefícios sociais já alcançados. A legenda precisa esclarecer o caráter conceitual, evitando associar pessoas e lugares reais a afirmações que a imagem não sustenta.

Antes de gerar, confira a licença do modelo e suas condições de uso. Rodar o software localmente não concede automaticamente direitos irrestritos sobre todos os possíveis resultados. Evite imitar pessoas identificáveis, documentos oficiais, marcas ou fotografias específicas sem autorização adequada.

Revise a saída em busca de elementos inadequados e detalhes que possam induzir o leitor ao erro. Uma legenda genérica não resolve todos os problemas de contexto. O texto alternativo deve descrever a função ilustrativa de maneira acessível.

Na automação editorial, mantenha o nome do modelo, o estado da tarefa e a identificação de conteúdo sintético. Se a geração falhar, não substitua silenciosamente o resultado por uma imagem aleatória nem publique como se estivesse pronta. Transparência sobre o processo é parte da qualidade do artigo, não apenas uma formalidade visual.""",
        ["https://www.nist.gov/itl/ai-risk-management-framework", "https://www.w3.org/WAI/tutorials/images/"],
        "Conceptual editorial artwork of a framed imaginary cosmic landscape next to abstract creative tools, clearly illustration about synthetic imagery, not a photograph, no people faces, no text or logos.",
    ),
]
