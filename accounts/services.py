import secrets
from django.utils import timezone
from core.network import fetch

def verify(domain):
    verification=domain.verification
    r=fetch(f'https://{domain.hostname}/{verification.key}.txt',max_redirects=0,same_host=domain.hostname)
    valid=r.status==200 and secrets.compare_digest(r.text.strip(),verification.key)
    verification.status='verified' if valid else 'failed'
    verification.checked_at=timezone.now(); verification.save()
    domain.status='verified' if valid else 'pending'
    domain.verified_at=timezone.now() if valid else None
    if not valid: domain.monitoring_enabled=False
    domain.save()
    return valid
