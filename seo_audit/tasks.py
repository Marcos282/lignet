from celery import shared_task
from django.db import transaction
from .models import SeoAudit,SeoIssue
from .services import audit,GUIDANCE
from core.security import record

@shared_task
def run_audit(audit_id):
    if not SeoAudit.objects.filter(pk=audit_id,status='pending').update(status='running'): return
    obj=SeoAudit.objects.get(pk=audit_id)
    try:
        report=audit(obj.url)
        with transaction.atomic():
            obj.report=report; obj.score=report['score']; obj.status='complete'; obj.save()
            for code,ok in report['checks'].items():
                if not ok:
                    severity,message,guidance=GUIDANCE[code]
                    SeoIssue.objects.create(audit=obj,code=code,severity=severity,message=message,guidance=guidance)
            if report['broken_links']:
                SeoIssue.objects.create(audit=obj,code='links',severity='attention',message='Links da amostra precisam de revisão',guidance='Confira os links listados; respostas não verificáveis não confirmam que o link está quebrado.')
        record('seo_audit','complete',obj.owner,obj.pk)
    except Exception:
        obj.status='failed'; obj.error='Não foi possível analisar a URL. Confira o domínio, o acesso público e o certificado HTTPS.'; obj.save()
        record('seo_audit','failed',obj.owner,obj.pk)
