import re
from core.network import normalize_url

def generate(agent,public,blocked,sitemap):
    agents=[a.strip() for a in agent.splitlines() if a.strip()]
    if not agents or any(not re.fullmatch(r'[A-Za-z0-9_*.-]{1,80}',a) for a in agents): raise ValueError('User-agent inválido.')
    lines=['# Gerado pelo Lignet SEO']+[f'User-agent: {a}' for a in agents]
    for action,values in [('Allow',public),('Disallow',blocked)]:
        for path in values.splitlines():
            path=path.strip()
            if not path: continue
            if not path.startswith('/') or any(c in path for c in ['\r','\n','#']) or len(path)>2048: raise ValueError('Informe caminhos iniciados por /, sem comentários.')
            lines.append(f'{action}: {path}')
    if sitemap.strip(): lines.extend(['', 'Sitemap: '+normalize_url(sitemap.strip())])
    return '\n'.join(lines)+'\n'
