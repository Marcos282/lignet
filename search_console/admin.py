from django.contrib import admin
from .models import SearchConsoleConnection
@admin.register(SearchConsoleConnection)
class ConnectionAdmin(admin.ModelAdmin):
    exclude = ('encrypted_tokens',)
