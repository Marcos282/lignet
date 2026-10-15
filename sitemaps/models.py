from django.db import models
from core.models import Owned
class SitemapGeneration(Owned):
    url_count = models.PositiveIntegerField()
    status = models.CharField(max_length=20,default='complete')
