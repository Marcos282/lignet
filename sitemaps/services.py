from xml.etree.ElementTree import Element, SubElement, tostring
from urllib.parse import urlsplit
from core.network import normalize_url

def generate(text):
    lines=text.splitlines()
    if len(lines)>50000: raise ValueError('Máximo de 50.000 URLs por sitemap.')
    urls=list(dict.fromkeys(normalize_url(x.strip()) for x in lines if x.strip()))
    if not urls: raise ValueError('Informe ao menos uma URL.')
    if len({urlsplit(x).netloc for x in urls})!=1: raise ValueError('Use URLs de um único domínio por arquivo.')
    root=Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for url in urls: SubElement(SubElement(root,'url'),'loc').text=url
    xml=tostring(root,encoding='utf-8',xml_declaration=True)
    if len(xml)>50*1024*1024: raise ValueError('Arquivo excede 50 MB.')
    return xml,len(urls)
