import secrets
from django.db import models
from core.models import Owned, Timestamped

def new_key(): return secrets.token_hex(24)
class Domain(Owned):
    hostname = models.CharField(max_length=253)
    status = models.CharField(max_length=20,default='pending',db_index=True)
    verified_at = models.DateTimeField(null=True,blank=True)
    monitoring_enabled = models.BooleanField(default=False)
    last_indexnow_at = models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['owner','hostname'],name='unique_owner_domain')]
    def __str__(self): return self.hostname
class DomainVerification(Timestamped):
    domain = models.OneToOneField(Domain,on_delete=models.CASCADE,related_name='verification')
    key = models.CharField(max_length=64,default=new_key,unique=True)
    status = models.CharField(max_length=20,default='pending')
    checked_at = models.DateTimeField(null=True,blank=True)
