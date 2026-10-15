import json
import secrets
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render,get_object_or_404
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET,require_POST
from .forms import MeasurementForm
from .models import Measurement,GlobalpingPolicy
from .limits import limit_request,LimitExceeded
from .tasks import create_measurement

PAGES={
    'ping-mundial':('Ping Mundial Grátis — Teste IPs e Sites de Vários Países','Teste ping online, latência internacional e perda de pacotes com sondas reais da Globalping. Compare países em um mapa interativo.','ping'),
    'traceroute-mundial':('Traceroute Online Mundial — Compare Rotas Internacionais','Veja os saltos, IPs e latências de rotas a partir de vários países com o traceroute mundial gratuito do Lignet.','traceroute'),
    'dns-mundial':('Teste DNS Mundial — Verificar Propagação DNS','Compare registros A, AAAA, MX, NS, TXT e CNAME entre regiões. Consulte resolvers e identifique diferenças nas respostas DNS.','dns'),
    'http-mundial':('Disponibilidade de Sites — Teste HTTP Mundial','Verifique status HTTP e tempos de conexão de sites a partir de diferentes regiões com medições reais da Globalping.','http'),
}


def private_json(data,status=200):
    response=JsonResponse(data,status=status)
    response['Cache-Control']='private, no-store'
    response['X-Robots-Tag']='noindex, nofollow, noarchive'
    response['Referrer-Policy']='strict-origin-when-cross-origin'
    return response


def identity(request):
    nonce=request.session.get('globalping_identity')
    if not nonce:
        nonce=secrets.token_urlsafe(32)
        request.session['globalping_identity']=nonce
    return salted_hmac('globalping.session',nonce,algorithm='sha256').hexdigest()


def permitted(request):
    query=Q(session_hash=identity(request))
    if request.user.is_authenticated: query|=Q(owner=request.user)
    return Measurement.objects.filter(query,expires_at__gt=timezone.now())


def rate_guard(request,policy,read=False):
    try:
        limit_request(request,policy.reads_per_hour if read else policy.requests_per_hour,'reads' if read else 'starts')
    except LimitExceeded as exc:
        response=private_json({'error':str(exc),'retry_after':exc.retry_after},429)
        response['Retry-After']=str(exc.retry_after)
        return response
    except Exception:
        return private_json({'error':'O controle de uso está indisponível. Tente mais tarde.'},503)


@require_GET
@ensure_csrf_cookie
def page(request,slug='ping-mundial'):
    title,description,kind=PAGES[slug]
    policy=GlobalpingPolicy.current()
    form=MeasurementForm(policy=policy,initial={'kind':kind})
    response=render(request,'globalping/page.html',{'title':title,'description':description,'slug':slug,'kind':kind,'form':form,'policy':policy,'map_config':{'tileUrl':settings.GLOBALPING_TILE_URL,'attribution':settings.GLOBALPING_TILE_ATTRIBUTION}})
    # OSM requires a valid cross-origin Referer, with normal browser tile caching.
    response['Referrer-Policy']='strict-origin-when-cross-origin'
    return response


@require_POST
def start(request):
    policy=GlobalpingPolicy.current()
    guarded=rate_guard(request,policy)
    if guarded is not None: return guarded
    if not policy.enabled: return private_json({'error':'Ferramenta temporariamente desativada pelo administrador.'},503)
    try: policy.full_clean()
    except ValidationError: return private_json({'error':'Configuração indisponível. Avise o administrador.'},503)
    if request.content_type!='application/json': return private_json({'error':'Use JSON para iniciar uma medição.'},415)
    if len(request.body)>8192: return private_json({'error':'Solicitação muito grande.'},413)
    try:
        data=json.loads(request.body) if request.content_type=='application/json' else request.POST
        if not isinstance(data,dict) and not hasattr(data,'getlist'): raise ValueError()
    except (ValueError,UnicodeError): return private_json({'error':'JSON inválido.'},400)
    form=MeasurementForm(data,policy=policy)
    if not form.is_valid(): return private_json({'error':'Revise os campos informados.','fields':form.errors.get_json_data()},400)
    obj=Measurement.objects.create(owner=request.user if request.user.is_authenticated else None,session_hash=identity(request),kind=form.cleaned_data['kind'],target=form.cleaned_data['target'],payload=form.cleaned_data['payload'],probes_requested=form.cleaned_data['probes'],expires_at=timezone.now()+timedelta(hours=policy.history_hours))
    try: create_measurement.delay(str(obj.pk))
    except Exception:
        obj.status='failed';obj.error='Fila temporariamente indisponível. Nenhum teste foi iniciado.';obj.save()
        return private_json({'error':obj.error,'id':str(obj.pk)},503)
    return private_json({'id':str(obj.pk),'status':obj.status},202)


def serialize(obj,details=False):
    data={'id':str(obj.pk),'type':obj.kind,'target':obj.target,'status':obj.status,'created_at':obj.created_at.isoformat(),'expires_at':obj.expires_at.isoformat(),'measured_at':obj.measured_at.isoformat() if obj.measured_at else None,'from_cache':obj.from_cache,'probes_requested':obj.probes_requested,'probes_count':obj.probes_count,'error':obj.error,'retry_after':obj.retry_after}
    if details:
        data.update(results=obj.results,remote_id=obj.remote_id,usage={'consumed':obj.consumed,'remaining':obj.remaining,'reset':obj.quota_reset,'limit':obj.quota_limit},poll_after=2)
    return data


@require_GET
def status(request,pk):
    policy=GlobalpingPolicy.current()
    guarded=rate_guard(request,policy,read=True)
    if guarded is not None: return guarded
    obj=get_object_or_404(permitted(request),pk=pk)
    # Reading local status can never create or poll an external measurement.
    return private_json(serialize(obj,details=True))


@require_GET
def history(request):
    policy=GlobalpingPolicy.current()
    guarded=rate_guard(request,policy,read=True)
    if guarded is not None: return guarded
    return private_json({'measurements':[serialize(obj) for obj in permitted(request)[:20]],'history_hours':policy.history_hours})
