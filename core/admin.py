from django.contrib import admin
from .models import BlockedHost, Activity
admin.site.register(BlockedHost)
admin.site.register(Activity)
