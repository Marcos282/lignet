from django.db import models
from core.models import Timestamped
class MonitoringCheck(Timestamped):
    domain = models.ForeignKey('accounts.Domain',on_delete=models.CASCADE,related_name='checks')
    status = models.CharField(max_length=20,default='pending',db_index=True)
    report = models.JSONField(default=dict)
    alerts = models.JSONField(default=list)
    class Meta: indexes = [models.Index(fields=['domain','-created_at'])]
