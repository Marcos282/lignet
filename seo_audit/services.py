import json
from urllib.parse import urljoin,urlsplit,urlunsplit
from bs4 import BeautifulSoup
from django.conf import settings
from core.network import fetch,normalize_url

# Fixed weights sum to 100; unavailable optional metrics do not affect score.
WEIGHTS={'http':20,'title':10,'description':10,'headings':10,'alt':5,'canonical':5,'indexable':10,'sitemap':5,'robots':5,'schema':5,'https':5,'social':5,'viewport':5}

def inspect_html(response):
    soup=BeautifulSoup(response.body,'html.parser')
    def meta(name):
        tag=soup.find('meta',attrs={'name':name}) or soup.find('meta',attrs={'property':name})
        return str(tag.get('content','')) if tag else ''
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    description=meta('description')
    headings=[{'level':int(t.name[1]),'text':t.get_text(' ',strip=True)[:200]} for t in soup.find_all(['h1','h2','h3'])]
    hierarchy=all(b['level']<=a['level']+1 for a,b in zip(headings,headings[1:]))
    images=soup.find_all('img'); missing=sum(1 for img in images if not img.has_attr('alt'))
    canonical=soup.find('link',rel='canonical')
    robots=' '.join([meta('robots'),meta('googlebot'),meta('bingbot'),response.headers.get('x-robots-tag','')])
    links=[]
    for tag in soup.find_all('a',href=True):
        try: links.append(normalize_url(urljoin(response.url,tag['href'])))
        except ValueError: continue
    links=list(dict.fromkeys(links))
    host=urlsplit(response.url).hostname
    internal=[u for u in links if urlsplit(u).hostname==host]
    schema=False
    for tag in soup.find_all('script',type='application/ld+json'):
        try:
            data=json.loads(tag.string or tag.get_text())
            schema=schema or 'schema.org' in json.dumps(data)
        except (ValueError,TypeError): pass
    schema=schema or any('schema.org/' in tag.get('itemtype','') for tag in soup.find_all(attrs={'itemtype':True}))
    checks={'http':200<=response.status<300,'title':30<=len(title)<=60,'description':70<=len(description)<=160,'headings':sum(h['level']==1 for h in headings)==1 and hierarchy,'alt':missing==0,'canonical':bool(canonical and canonical.get('href')),'indexable':not any(x in robots.lower() for x in ('noindex','none')),'schema':schema,'https':urlsplit(response.url).scheme=='https','social':bool(meta('og:title') and meta('og:description') and meta('og:image') and meta('twitter:card')),'viewport':'width=device-width' in meta('viewport').replace(' ','').lower()}
    return {'url':response.url,'http_status':response.status,'title':title,'title_length':len(title),'description':description,'description_length':len(description),'headings':headings,'missing_alt':missing,'image_count':len(images),'internal_links':internal[:200],'external_link_count':len(links)-len(internal),'canonical':canonical.get('href','') if canonical else '', 'robots_directives':robots.strip(),'checks':checks,'response_seconds':response.elapsed,'redirects':response.redirects,'certificate_expires':response.certificate_expires,'mobile':'Viewport detectado; compatibilidade visual não foi testada.' if checks['viewport'] else 'Sem evidência suficiente de compatibilidade móvel.'}

GUIDANCE={
'http':('critical','Página indisponível','Corrija o servidor para retornar uma resposta HTTP 2xx.'),
'title':('attention','Revise o título da página','Crie um título descritivo; a faixa interna usada nesta auditoria é de 30 a 60 caracteres.'),
'description':('attention','Revise a meta description','Descreva o conteúdo com clareza; usamos a faixa de 70 a 160 caracteres como referência editorial.'),
'headings':('attention','Revise a hierarquia de títulos','Use um H1 principal e organize H2 e H3 sem pular níveis.'),
'alt':('attention','Há imagens sem atributo alt','Descreva imagens informativas e use alt vazio para imagens decorativas.'),
'canonical':('recommendation','Canonical não encontrada','Informe uma URL canônica coerente no HTML.'),
'indexable':('critical','Diretiva de bloqueio à indexação','Confira se noindex é intencional antes de alterar a meta tag ou X-Robots-Tag.'),
'sitemap':('attention','Sitemap padrão indisponível','Publique um sitemap XML válido e informe seu endereço no robots.txt.'),
'robots':('recommendation','robots.txt indisponível','Publique as instruções de rastreamento na raiz do domínio.'),
'schema':('recommendation','Dados estruturados não detectados','Adicione Schema.org apropriado ao conteúdo e valide sua sintaxe.'),
'https':('critical','HTTPS não detectado','Configure TLS válido e redirecione HTTP para HTTPS.'),
'social':('recommendation','Metadados sociais incompletos','Configure Open Graph e Twitter Cards para melhorar o compartilhamento.'),
'viewport':('attention','Viewport responsivo ausente','Adicione meta viewport e confira o layout em dispositivos reais.')}

def audit(url):
    response=fetch(url)
    if 'html' not in response.headers.get('content-type','').lower(): raise ValueError('A URL deve retornar uma página HTML.')
    report=inspect_html(response)
    p=urlsplit(response.url); root=urlunsplit((p.scheme,p.netloc,'/','',''))
    for name,path in [('sitemap','sitemap.xml'),('robots','robots.txt')]:
        try:
            r=fetch(urljoin(root,path),same_host=p.hostname)
            valid=r.status==200
            if name=='sitemap':
                from xml.etree.ElementTree import fromstring
                valid=valid and fromstring(r.body).tag.split('}')[-1] in ('urlset','sitemapindex')
            else: valid=valid and '<html' not in r.text.lower() and 'user-agent:' in r.text.lower()
            report['checks'][name]=valid
        except Exception: report['checks'][name]=False
    report['broken_links']=[]; report['unchecked_links']=len(report['internal_links'])
    # Public audit: bounded sample on the original host only; no recursive crawl.
    for link in report['internal_links'][:settings.MAX_LINK_CHECKS]:
        try:
            result=fetch(link,method='HEAD',same_host=p.hostname)
            if result.status>=400: report['broken_links'].append({'url':link,'status':result.status})
        except Exception: report['broken_links'].append({'url':link,'status':'não verificável'})
        report['unchecked_links']-=1
    try:
        http_probe=fetch(urlunsplit(('http',p.netloc,p.path or '/',p.query,'')),method='HEAD',same_host=p.hostname)
        report['http_to_https']={'verified':urlsplit(http_probe.url).scheme=='https','status':http_probe.status,'redirects':http_probe.redirects}
    except Exception:
        report['http_to_https']={'verified':None,'note':'Não foi possível verificar o redirecionamento HTTP para HTTPS.'}
    report['performance']={'status':'indisponível','note':'Tempo HTTP não equivale a Core Web Vitals. Configure PageSpeed Insights para métricas adicionais.'}
    if settings.PAGESPEED_API_KEY:
        try:
            import requests
            r=requests.get('https://www.googleapis.com/pagespeedonline/v5/runPagespeed',params={'url':response.url,'key':settings.PAGESPEED_API_KEY,'strategy':'mobile','category':'performance'},timeout=45,allow_redirects=False)
            r.raise_for_status(); data=r.json()
            report['performance']={'status':'disponível','lab_score':data.get('lighthouseResult',{}).get('categories',{}).get('performance',{}).get('score'),'field':data.get('loadingExperience',{}).get('metrics',{})}
        except Exception: report['performance']['note']='API indisponível ou quota excedida; nenhuma métrica foi inventada.'
    report['score']=sum(weight for key,weight in WEIGHTS.items() if report['checks'].get(key))
    return report
