from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from .models import (Article, Category, EditorialEvent, EditorialRun, EditorialSettings,
                     Keyword, NewsItem, Photo, PublicationSlot, Source)
from .services import approve, event, withdraw


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status", "manual_approval", "cover", "generated", "scheduled_at", "published_at"]
    list_filter = ["status", "manual_approval", "category", "generated"]
    search_fields = ["title", "body", "keywords__name"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["keywords"]
    readonly_fields = ["status", "approved_at", "published_at", "generated", "item", "created_at", "updated_at",
                       "image_job", "image_model", "image_requested_at", "image_retry_at"]
    actions = ["approve_articles", "withdraw"]

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Aprovar e reservar próximos horários disponíveis", permissions=["approve"])
    def approve_articles(self, request, queryset):
        config = EditorialSettings.current()
        count = 0
        for article in queryset.order_by("created_at"):
            if article.status not in ("draft", "pending"):
                continue
            try:
                approve(article, config)
                count += 1
            except (ValueError, ValidationError) as exc:
                event(None, "approve", f"Artigo #{article.pk}: aprovação recusada; confira foto e horários.", error=True, article=article)
                self.message_user(request, f"{article.title}: {exc}", messages.ERROR)
        self.message_user(request, f"{count} artigos aprovados e agendados. A publicação depende do Cron e da rotina habilitada.")

    def has_approve_permission(self, request):
        return request.user.has_perm("blog.approve_article")

    @admin.action(description="Retirar manualmente (não republicar automaticamente)", permissions=["approve"])
    def withdraw(self, request, queryset):
        for article in queryset:
            withdraw(article)

    def save_model(self, request, obj, form, change):
        if change and form.changed_data and obj.status != "withdrawn":
            obj.status = "pending"
            obj.approved_at = None
            obj.scheduled_at = None
            notice = ("Alterações aguardando sua aprovação manual." if obj.manual_approval
                      else "Alterações enviadas novamente ao fluxo editorial automático.")
            self.message_user(request, notice, messages.WARNING)
        super().save_model(request, obj, form, change)
        event(None, "edit", "Artigo salvo no painel.", article=obj)


@admin.register(EditorialSettings)
class EditorialSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return super().has_add_permission(request) and not EditorialSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "enabled", "authorized", "allow_auto_publish", "last_collected_at"]
    readonly_fields = ["last_collected_at"]
    list_filter = ["enabled", "authorized"]
    search_fields = ["name", "feed_url"]


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "credit", "generated", "rights_confirmed", "allow_automatic"]
    list_filter = ["category", "allow_automatic", "generated"]
    readonly_fields = ["generated", "model_name"]
    search_fields = ["title", "alt", "credit"]


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ["title", "source", "score", "state", "created_at"]
    list_filter = ["state", "source"]
    search_fields = ["title"]
    readonly_fields = ["source", "title", "url", "fingerprint", "summary", "score", "created_at", "updated_at"]

    def has_add_permission(self, request):
        return False


class HistoryAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EditorialRun)
class RunAdmin(HistoryAdmin):
    list_display = ["started_at", "finished_at", "status", "found", "produced", "published"]
    list_filter = ["status"]


@admin.register(EditorialEvent)
class EventAdmin(HistoryAdmin):
    list_display = ["created_at", "stage", "level", "article", "message"]
    list_filter = ["level", "stage"]
    search_fields = ["message"]


admin.site.register(Category)
admin.site.register(Keyword)
admin.site.register(PublicationSlot)
