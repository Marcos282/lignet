import uuid
from django.db import models
from django.conf import settings
from core.models import Timestamped
class SeoAudit(Timestamped):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    url = models.URLField(max_length=2048)
    status = models.CharField(max_length=20,default='pending',db_index=True)
    score = models.PositiveSmallIntegerField(null=True,blank=True)
    report = models.JSONField(default=dict)
    error = models.CharField(max_length=300,blank=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(score__gte=0,score__lte=100)|models.Q(score__isnull=True),name='audit_score_range')]
class SeoIssue(Timestamped):
    audit = models.ForeignKey(SeoAudit,on_delete=models.CASCADE,related_name='issues')
    code = models.CharField(max_length=80)
    severity = models.CharField(max_length=20,choices=[('critical','Crítico'),('attention','Atenção'),('recommendation','Recomendação')])
    message = models.CharField(max_length=300)
    guidance = models.TextField()

    class Meta:
        ordering = ['severity', 'created_at']
