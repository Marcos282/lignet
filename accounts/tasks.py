from celery import shared_task
from .models import Domain
from .services import verify
from core.security import record

@shared_task
def verify_domain(domain_id):
    domain=Domain.objects.get(pk=domain_id)
    try: valid=verify(domain)
    except Exception: valid=False
    if not valid:
        domain.status='pending'; domain.verified_at=None; domain.monitoring_enabled=False; domain.save()
    record('domain_verification','verified' if valid else 'failed',domain.owner,domain.pk)
