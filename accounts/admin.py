from django.contrib import admin
from .models import Domain, DomainVerification
admin.site.register(Domain)
admin.site.register(DomainVerification)
