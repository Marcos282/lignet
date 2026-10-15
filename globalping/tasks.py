from datetime import timedelta
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from core.security import record
from .models import Measurement,GlobalpingPolicy
from .services import GlobalpingClient,APIError
from .validation import target,validate_dns
from .limits import reserve_probes,fingerprint,LimitExceeded,backoff
from .results import normalize

TERMINAL=('finished','failed','expired')


def fail(obj,message,retry_after=None,status=None,usage=None):
    obj.status='failed'; obj.error=message; obj.retry_after=retry_after
    if status: obj.response_status=status
    if usage:
        for field,value in usage.items(): setattr(obj,field,value)
    obj.save()
    record('globalping','failed',obj.owner,obj.pk)


def enqueue_poll(obj,policy,delay=None):
    try: poll_measurement.apply_async(args=[str(obj.pk)],countdown=delay or policy.poll_seconds)
    except Exception: fail(obj,'Não foi possível consultar o progresso. O teste não será reenviado.')


@shared_task
def create_measurement(measurement_id):
    if not Measurement.objects.filter(pk=measurement_id,status='queued').update(status='validating'): return
    obj=Measurement.objects.get(pk=measurement_id)
    policy=GlobalpingPolicy.current()
    try:
        policy.full_clean()
        if not policy.enabled: raise ValueError('Ferramenta temporariamente desativada.')
        if obj.expires_at<=timezone.now(): raise ValueError('Solicitação expirada.')
        if not 1<=obj.probes_requested<=min(50,policy.max_probes): raise ValueError('Limite de sondas alterado. Inicie outro teste.')
        host,_,_=target(obj.target,obj.kind)
        validate_dns(host,obj.kind)
        if (timezone.now()-obj.created_at).total_seconds()>policy.timeout_seconds or not Measurement.objects.filter(pk=obj.pk,status='validating').exists():
            raise ValueError('A solicitação expirou antes do envio. Inicie outro teste.')
        key='gp:result:'+fingerprint(obj.payload)
        cached=cache.get(key)
        if cached:
            obj.remote_id=cached['remote_id'];obj.results=cached['results'];obj.probes_count=cached['probes_count'];obj.measured_at=cached['measured_at'];obj.from_cache=True;obj.status='finished';obj.consumed=0;obj.save()
            return
        reserve_probes(obj.probes_requested,policy)
        # POST is intentionally never retried: timeouts could hide accepted tests.
        obj.status='creating';obj.save(update_fields=['status','updated_at'])
        result=GlobalpingClient().create(obj.payload)
        obj.remote_id=result.data['id'];obj.probes_count=result.data['probesCount'];obj.response_status=result.status;obj.status='in-progress'
        for field,value in result.usage.items(): setattr(obj,field,value)
        obj.save()
        record('globalping_created','in-progress',obj.owner,obj.pk)
    except APIError as exc:
        if exc.status==429: backoff(exc.retry_after)
        fail(obj,str(exc),exc.retry_after,exc.status,exc.usage);return
    except (ValueError,LimitExceeded) as exc:
        fail(obj,str(exc),getattr(exc,'retry_after',None));return
    except Exception:
        fail(obj,'Serviço de filas, cache ou comunicação indisponível. Nenhum reenvio automático será feito.');return
    enqueue_poll(obj,policy)


@shared_task
def poll_measurement(measurement_id):
    obj=Measurement.objects.filter(pk=measurement_id,status='in-progress').first()
    if not obj: return
    policy=GlobalpingPolicy.current()
    if not policy.enabled:
        fail(obj,'A ferramenta foi desativada pelo administrador.');return
    if (timezone.now()-obj.created_at).total_seconds()>policy.timeout_seconds or obj.poll_count>=90:
        fail(obj,'Tempo limite atingido ao aguardar a medição. Resultados parciais, se houver, foram preservados.');return
    try:
        # Duplicate deliveries cannot increase upstream polling above our interval.
        if not cache.add('gp:poll:'+str(obj.pk),True,max(1,policy.poll_seconds)): return
        if not cache.add('gp:poll-lock:'+str(obj.pk),True,25): return
    except Exception:
        fail(obj,'Cache temporariamente indisponível.');return
    next_delay=policy.poll_seconds
    try:
        result=GlobalpingClient().get(obj.remote_id,obj.etag)
        obj.poll_count+=1
        if result.status!=304:
            data=result.data
            if data.get('id')!=obj.remote_id or data.get('type')!=obj.kind or not isinstance(data.get('results'),list) or not isinstance(data.get('status'),str):
                raise APIError('Formato de resposta inesperado da Globalping.')
            obj.results=normalize(data,obj.kind);obj.etag=result.etag
            if isinstance(data.get('createdAt'),str):
                measured=parse_datetime(data['createdAt'])
                if measured and timezone.is_aware(measured): obj.measured_at=measured
            # Official rule: any status other than in-progress is terminal.
            if data['status']!='in-progress': obj.status='finished'
        obj.save()
        if obj.status=='finished':
            cache.set('gp:result:'+fingerprint(obj.payload),{'remote_id':obj.remote_id,'results':obj.results,'probes_count':obj.probes_count,'measured_at':obj.measured_at},policy.cache_seconds)
            record('globalping','finished',obj.owner,obj.pk)
    except APIError as exc:
        if exc.status==429:
            obj.poll_count+=1;obj.retry_after=exc.retry_after;obj.save()
            next_delay=max(policy.poll_seconds,exc.retry_after or 5)
        else:
            fail(obj,str(exc),exc.retry_after,exc.status);return
    except Exception:
        fail(obj,'Não foi possível processar a resposta da Globalping.');return
    finally:
        cache.delete('gp:poll-lock:'+str(obj.pk))
    if obj.status=='in-progress': enqueue_poll(obj,policy,next_delay)


@shared_task
def expire_stalled():
    policy=GlobalpingPolicy.current()
    cutoff=timezone.now()-timedelta(seconds=policy.timeout_seconds+30)
    Measurement.objects.filter(status__in=['queued','validating','creating','in-progress'],created_at__lt=cutoff).update(status='failed',error='A tarefa expirou. Nenhum novo teste foi enviado automaticamente.')


@shared_task
def cleanup():
    Measurement.objects.filter(expires_at__lt=timezone.now()).delete()
