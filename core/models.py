from django.db import models
from django.conf import settings
class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: abstract = True
class Owned(Timestamped):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    class Meta: abstract = True
class BlockedHost(Timestamped):
    hostname = models.CharField(max_length=253,unique=True)
    reason = models.CharField(max_length=300)
    def __str__(self): return self.hostname
class Activity(Timestamped):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    event = models.CharField(max_length=80,db_index=True)
    status = models.CharField(max_length=32)
    object_id = models.CharField(max_length=80,blank=True)
