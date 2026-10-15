import re
import unicodedata


def normalized(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


TOOLS = [
    {"name": "Ping mundial", "url": "/ferramentas/ping-mundial/",
     "terms": ["ping", "latência", "conectividade", "perda de pacotes", "roteamento", "traceroute"]},
    {"name": "Calculadora CIDR", "url": "/ferramentas/calculadora-cidr/",
     "terms": ["ipv4", "ipv6", "cidr", "sub-rede", "endereçamento", "máscara"]},
    {"name": "Consultar DNS", "url": "/ferramentas/consultar-dns/",
     "terms": ["dns", "domínio", "resolução", "registro a", "registro mx"]},
    {"name": "Analisador SEO", "url": "/ferramentas/seo/",
     "terms": ["seo", "indexação", "canonical", "metatag", "search console", "google"]},
    {"name": "Redutor de imagens", "url": "/#redutor",
     "terms": ["imagem", "imagens", "webp", "jpeg", "png", "compressão"]},
    {"name": "Gerador de QR Code", "url": "/#qrcode",
     "terms": ["qr code", "qrcode", "código qr"]},
]


def matches(text, terms):
    text = normalized(text)
    return sum(bool(re.search(r"(?<!\w)" + re.escape(normalized(term.strip())) + r"(?!\w)", text))
               for term in terms if term.strip())


def recommended_tools(text):
    ranked = [(matches(text, tool["terms"]), tool) for tool in TOOLS]
    return [tool for score, tool in sorted(ranked, key=lambda pair: pair[0], reverse=True) if score][:3]
