from django.contrib import admin
from .models import GlobalpingPolicy, Measurement


@admin.register(GlobalpingPolicy)
class PolicyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return super().has_add_permission(request) and not GlobalpingPolicy.objects.exists()
    def has_delete_permission(self, request, obj=None): return False


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ('created_at','kind','target','status','probes_requested','probes_count','consumed','from_cache')
    list_filter = ('status','kind','from_cache')
    search_fields = ('target','remote_id')
    readonly_fields = [field.name for field in Measurement._meta.fields]
    def has_add_permission(self, request): return False
