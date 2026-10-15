from django.db import models
from core.models import Owned
class SearchConsoleConnection(Owned):
    domain = models.OneToOneField('accounts.Domain',on_delete=models.CASCADE,related_name='search_console')
    property_url = models.CharField(max_length=2048)
    encrypted_tokens = models.TextField()
    status = models.CharField(max_length=20,default='connected')
    data = models.JSONField(default=dict)
