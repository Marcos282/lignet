import secrets,time,hashlib,base64
from urllib.parse import urlencode,urlsplit
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404,redirect
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest
from accounts.models import Domain
from core.security import limited,record
from .models import SearchConsoleConnection
from .services import cipher,save_tokens
from .tasks import sync

@login_required
@require_POST
@limited()
def connect(request,pk):
    domain=get_object_or_404(Domain,pk=pk,owner=request.user,status='verified')
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.TOKEN_ENCRYPTION_KEY:
        messages.error(request,'Integração Google ainda não configurada pelo administrador.')
        return redirect('dashboard')
    cipher()
    state=secrets.token_urlsafe(32); verifier=secrets.token_urlsafe(64)
    request.session['google_oauth']={'state':state,'domain':domain.pk,'created':time.time(),'verifier':verifier}
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    params={'client_id':settings.GOOGLE_CLIENT_ID,'redirect_uri':settings.GOOGLE_REDIRECT_URI,'response_type':'code','scope':'https://www.googleapis.com/auth/webmasters','access_type':'offline','prompt':'consent','state':state,'code_challenge':challenge,'code_challenge_method':'S256'}
    return redirect('https://accounts.google.com/o/oauth2/v2/auth?'+urlencode(params))

@login_required
def callback(request):
    state=request.session.pop('google_oauth',None)
    if not state or time.time()-state['created']>600 or not secrets.compare_digest(state['state'],request.GET.get('state','')):
        return HttpResponseBadRequest('Estado OAuth inválido ou expirado.')
    domain=get_object_or_404(Domain,pk=state['domain'],owner=request.user,status='verified')
    try:
        if request.GET.get('error') or not request.GET.get('code'): raise ValueError()
        r=requests.post('https://oauth2.googleapis.com/token',data={'client_id':settings.GOOGLE_CLIENT_ID,'client_secret':settings.GOOGLE_CLIENT_SECRET,'code':request.GET['code'],'code_verifier':state['verifier'],'grant_type':'authorization_code','redirect_uri':settings.GOOGLE_REDIRECT_URI},timeout=15,allow_redirects=False)
        r.raise_for_status(); tokens=r.json()
        r=requests.get('https://www.googleapis.com/webmasters/v3/sites',headers={'Authorization':'Bearer '+tokens['access_token']},timeout=15,allow_redirects=False)
        r.raise_for_status()
        # Restrict to the exact verified host; Google itself must grant owner access.
        properties=[x['siteUrl'] for x in r.json().get('siteEntry',[]) if x.get('permissionLevel')=='siteOwner' and x.get('siteUrl') in ('sc-domain:'+domain.hostname,'https://'+domain.hostname+'/')]
        if not properties: raise ValueError('Nenhuma propriedade autorizada.')
        obj,_=SearchConsoleConnection.objects.get_or_create(domain=domain,owner=request.user,defaults={'property_url':properties[0]})
        obj.property_url=properties[0]; obj.status='connected'; save_tokens(obj,tokens)
        record('oauth_connected','complete',request.user,obj.pk)
        messages.success(request,'Search Console conectado. Use Atualizar dados para consultar a propriedade.')
    except Exception:
        record('oauth_connected','failed',request.user,domain.pk)
        messages.error(request,'Não foi possível conectar. Confirme as credenciais e a propriedade no Google.')
    return redirect('dashboard')

@login_required
@require_POST
@limited()
def refresh(request,pk):
    obj=get_object_or_404(SearchConsoleConnection,domain_id=pk,owner=request.user,domain__status='verified')
    try:
        sitemap=request.POST.get('sitemap','').strip()
        if sitemap:
            from core.network import normalize_url
            sitemap=normalize_url(sitemap)
            if urlsplit(sitemap).hostname!=obj.domain.hostname: raise ValueError()
        sync.delay(obj.pk,sitemap)
        messages.success(request,'Atualização enviada à fila.')
    except Exception: messages.error(request,'Não foi possível enfileirar. Confira o sitemap e o serviço de filas.')
    return redirect('dashboard')

@login_required
@require_POST
@limited()
def disconnect(request,pk):
    obj=get_object_or_404(SearchConsoleConnection,domain_id=pk,owner=request.user)
    # Local deletion removes encrypted credentials. Google account access can also be revoked in account settings.
    obj.delete(); record('oauth_disconnected','complete',request.user,pk)
    messages.success(request,'Conexão e tokens locais removidos. Você também pode revogar o acesso na sua conta Google.')
    return redirect('dashboard')
