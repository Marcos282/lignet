import requests
from celery import shared_task
from .models import IndexNowSubmission
from accounts.services import verify
from core.network import normalize_url
from core.security import record
from urllib.parse import urlsplit

@shared_task
def submit(submission_id):
    if not IndexNowSubmission.objects.filter(pk=submission_id,status='pending').update(status='running'): return
    obj=IndexNowSubmission.objects.select_related('domain','owner').get(pk=submission_id)
    try:
        domain=obj.domain
        if domain.owner_id!=obj.owner_id or domain.status!='verified' or not verify(domain): raise ValueError('Propriedade não validada')
        urls=[normalize_url(u) for u in obj.urls]
        if not urls or len(urls)>10000 or any(urlsplit(u).hostname!=domain.hostname for u in urls): raise ValueError('URLs fora do domínio')
        key=domain.verification.key
        r=requests.post('https://api.indexnow.org/indexnow',json={'host':domain.hostname,'key':key,'keyLocation':f'https://{domain.hostname}/{key}.txt','urlList':urls},timeout=15,allow_redirects=False)
        obj.response_code=r.status_code
        obj.status='accepted' if r.status_code==200 else ('validation_pending' if r.status_code==202 else 'failed')
        obj.response_detail='Recebido; não garante indexação.' if r.status_code in (200,202) else 'Serviço recusou o envio. Confira a chave, a quota e as URLs.'
    except Exception:
        obj.status='failed'; obj.response_detail='Falha na verificação de propriedade ou comunicação com IndexNow.'
    obj.save(); record('indexnow',obj.status,obj.owner,obj.pk)
