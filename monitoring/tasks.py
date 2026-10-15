from datetime import timedelta,datetime,timezone as dt_timezone
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from accounts.models import Domain
from accounts.services import verify
from .models import MonitoringCheck
from seo_audit.services import audit
from core.security import record

@shared_task
def schedule_checks():
    cutoff=timezone.now()-timedelta(hours=settings.MONITOR_INTERVAL_HOURS)
    for pk in Domain.objects.filter(status='verified',monitoring_enabled=True).values_list('pk',flat=True):
        with transaction.atomic():
            domain=Domain.objects.select_for_update().get(pk=pk)
            # A single Beat scheduler is required; row lock also prevents duplicate enqueue.
            if domain.checks.filter(created_at__gte=cutoff).exists(): continue
            check=MonitoringCheck.objects.create(domain=domain)
            transaction.on_commit(lambda c=check.pk: run_check.delay(c))

@shared_task
def run_check(check_id):
    if not MonitoringCheck.objects.filter(pk=check_id,status='pending').update(status='running'): return
    check=MonitoringCheck.objects.select_related('domain').get(pk=check_id)
    try:
        if not check.domain.monitoring_enabled or not verify(check.domain): raise ValueError('Domínio não autorizado')
        previous=check.domain.checks.filter(status='complete').exclude(pk=check.pk).order_by('-created_at').first()
        check.report=audit('https://'+check.domain.hostname+'/')
        check.alerts=[]
        if previous:
            for key in ('title','description','robots_directives'):
                if previous.report.get(key)!=check.report.get(key): check.alerts.append('Alteração detectada: '+key)
        for key in ('http','https','sitemap','indexable'):
            if not check.report['checks'].get(key): check.alerts.append('Revisar: '+key)
        expiry=check.report.get('certificate_expires')
        if expiry:
            expires=datetime.strptime(expiry,'%b %d %H:%M:%S %Y %Z').replace(tzinfo=dt_timezone.utc)
            if expires-timezone.now()<timedelta(days=14): check.alerts.append('Certificado HTTPS vence em menos de 14 dias.')
        check.status='complete'
    except Exception:
        check.status='failed'; check.alerts=['Falha de disponibilidade, certificado ou validação de propriedade.']
        if check.domain.checks.filter(status='failed').exclude(pk=check.pk).order_by('-created_at')[:2].count()>=2:
            check.alerts.append('Falhas recorrentes: revise o serviço.')
    check.save(); record('monitoring',check.status,check.domain.owner,check.pk)
