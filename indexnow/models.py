from django.db import models
from core.models import Owned
class IndexNowSubmission(Owned):
    domain = models.ForeignKey('accounts.Domain',on_delete=models.CASCADE,related_name='submissions')
    urls = models.JSONField(default=list)
    status = models.CharField(max_length=20,default='pending',db_index=True)
    response_code = models.PositiveSmallIntegerField(null=True,blank=True)
    response_detail = models.CharField(max_length=300,blank=True)
