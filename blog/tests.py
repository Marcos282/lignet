import json
from datetime import time, timedelta
from io import BytesIO, StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch
from xml.etree import ElementTree

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from bs4 import BeautifulSoup

from core.network import Response
from .admin import ArticleAdmin
from .initial_articles import ARTICLES
from .models import (Article, Category, EditorialEvent, EditorialRun, EditorialSettings,
                     Keyword, NewsItem, Photo, PublicationSlot, Source)
from .services import (approve, auto_approve_pending, collect_source, create_article,
                       execute_run, next_slot, ollama_generate, publish_due)
from .tools import recommended_tools


def photo_file(name="camera.png", size=(120, 80)):
    data = BytesIO()
    Image.new("RGB", size, "#1769e0").save(data, "PNG")
    return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")


class BlogTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.media = override_settings(MEDIA_ROOT=self.directory.name)
        self.media.enable()
        self.addCleanup(self.media.disable)
        self.category = Category.objects.create(name="Redes", slug="redes", topics="ping,dns,cidr")
        self.config = EditorialSettings.current()
        self.config.enabled = True
        self.config.generation_time = time(0)
        self.config.save()
        PublicationSlot.objects.create(time=time(23, 59))

    def photo(self):
        return Photo.objects.create(title="Equipamento", image=photo_file(),
                                    category=self.category, alt="Equipamento de rede", credit="Foto própria",
                                    rights_confirmed=True, allow_automatic=True)

    def article(self, **overrides):
        fields = dict(title="Como verificar a conectividade de uma rede", slug="guia-ping",
                      body="Texto original sobre ping e conectividade.\n\n" * 35,
                      excerpt="Um guia de diagnóstico com contexto, limitações e ferramentas para verificar sua rede.",
                      category=self.category, references=["https://www.rfc-editor.org/rfc/rfc792"])
        fields.update(overrides)
        return Article.objects.create(**fields)

    def item(self):
        source = Source.objects.create(name="Fonte autorizada", category=self.category,
                                       feed_url="https://example.org/rss", authorized=True)
        return NewsItem.objects.create(source=source, url="https://example.org/noticia",
                                      fingerprint="a" * 64, title="Ping em redes distribuídas",
                                      summary="Um breve contexto editorial sobre conectividade.", score=30)

    def payload(self):
        return {"title": "Como diagnosticar conectividade com medições comparáveis",
                "excerpt": "Um guia original para organizar a investigação de conectividade, registrar evidências e entender limites.",
                "body": "Compare destinos e horários sem atribuir a causa de uma falha sem evidências. " * 24}

    def test_seed_exact_twenty_original_idempotent(self):
        call_command("blog_seed", stdout=StringIO())
        call_command("blog_seed", stdout=StringIO())
        self.assertEqual(Article.objects.count(), 20)
        self.assertEqual(len(ARTICLES), 20)
        self.assertEqual(Article.objects.public().count(), 0)
        self.assertEqual(Article.objects.filter(status="pending").count(), 20)
        self.assertEqual(EditorialEvent.objects.filter(stage="seed").count(), 20)
        for article in Article.objects.all():
            article.full_clean()
            self.assertGreater(len(article.body), 1200)
            self.assertTrue(article.references)
            self.assertFalse(article.generated)

    def test_publication_requires_photo(self):
        article = self.article()
        with self.assertRaises(ValidationError):
            approve(article, self.config)
        article.refresh_from_db()
        self.assertEqual(article.status, "pending")

    def test_auto_approval_uses_authorized_own_photo(self):
        article = self.article()
        run = EditorialRun.objects.create()
        auto_approve_pending(self.config, run)
        article.refresh_from_db()
        self.assertEqual(article.status, "pending")
        self.assertEqual(EditorialEvent.objects.filter(stage="await_photo").count(), 1)
        auto_approve_pending(self.config, run)
        self.assertEqual(EditorialEvent.objects.filter(stage="await_photo").count(), 1)
        photo = self.photo()
        auto_approve_pending(self.config, run)
        article.refresh_from_db()
        self.assertEqual(article.status, "scheduled")
        self.assertEqual(article.cover, photo)
        self.assertIsNotNone(article.approved_at)

    def test_withdrawn_never_automatically_republished(self):
        self.photo()
        article = self.article(status="withdrawn")
        auto_approve_pending(self.config, EditorialRun.objects.create())
        article.refresh_from_db()
        self.assertEqual(article.status, "withdrawn")

    def test_source_can_disable_automatic_publication(self):
        item = self.item()
        item.source.allow_auto_publish = False
        item.source.save()
        article = self.article(item=item)
        self.photo()
        auto_approve_pending(self.config, EditorialRun.objects.create())
        article.refresh_from_db()
        self.assertEqual(article.status, "pending")

    def test_schedules_and_publication_daily_cap(self):
        self.config.daily_limit = 1
        self.config.save()
        photo = self.photo()
        first = self.article(cover=photo)
        second = self.article(slug="guia-dois", title="Outro guia original de endereçamento", cover=photo)
        approve(first, self.config)
        approve(second, self.config)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertNotEqual(timezone.localdate(first.scheduled_at), timezone.localdate(second.scheduled_at))
        Article.objects.update(scheduled_at=timezone.now() - timedelta(minutes=1))
        run = EditorialRun.objects.create()
        publish_due(self.config, run)
        self.assertEqual(Article.objects.public().count(), 1)
        publish_due(self.config, run)
        self.assertEqual(Article.objects.public().count(), 1)

    def test_future_schedule_never_published(self):
        article = self.article(cover=self.photo())
        approve(article, self.config)
        publish_due(self.config, EditorialRun.objects.create())
        article.refresh_from_db()
        self.assertEqual(article.status, "scheduled")

    def test_missing_slots_are_explicit_error(self):
        PublicationSlot.objects.all().delete()
        with self.assertRaisesMessage(ValueError, "horário"):
            next_slot(self.config)

    def test_manual_mode_leaves_pending(self):
        self.photo()
        article = self.article()
        self.config.automatic = False
        auto_approve_pending(self.config, EditorialRun.objects.create())
        article.refresh_from_db()
        self.assertEqual(article.status, "pending")

    def test_photos_are_reencoded_and_metadata_not_kept(self):
        photo = self.photo()
        self.assertTrue(photo.image.name.endswith(".jpg"))
        self.assertNotIn("camera", photo.image.name)
        with Image.open(photo.image) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertFalse(image.getexif())
        with self.assertRaises(ValidationError):
            Photo.objects.create(title="Não autorizada", image=photo_file(), category=self.category,
                                 alt="Teste", credit="Autor", rights_confirmed=False)
        with self.assertRaises(ValidationError):
            Photo.objects.create(title="Inválida", image=SimpleUploadedFile("x.svg", b"<svg/>"),
                                 category=self.category, alt="Teste", credit="Autor", rights_confirmed=True)

    def test_photo_limits(self):
        from .photos import normalize_photo
        with self.assertRaises(ValidationError):
            normalize_photo(SimpleUploadedFile("large.png", b"x" * (8 * 1024 * 1024 + 1)))
        with self.assertRaises(ValidationError):
            normalize_photo(photo_file(size=(12001, 1)))

    def test_pagination_seo_schema_related_and_hidden_articles(self):
        call_command("blog_seed", stdout=StringIO())
        cover = self.photo()
        Article.objects.update(status="published", cover=cover, approved_at=timezone.now(),
                               published_at=timezone.now())
        response = self.client.get("/blog/?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page"]), 6)
        self.assertContains(response, "/blog/?page=2", html=False)
        article = Article.objects.first()
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        schema = json.loads(soup.find("script", type="application/ld+json").string)
        self.assertEqual(schema["@type"], "BlogPosting")
        self.assertIn("image", schema)
        self.assertTrue(soup.find("meta", property="og:image"))
        self.assertContains(response, "Referências para conferir")
        self.assertContains(response, "Continue explorando")
        article.status = "withdrawn"
        article.save()
        self.assertEqual(self.client.get(article.get_absolute_url()).status_code, 404)
        sitemap = self.client.get("/blog/sitemap-artigos.xml")
        self.assertNotContains(sitemap, article.slug)
        self.assertEqual(len(ElementTree.fromstring(sitemap.content)), 19)
        self.assertContains(self.client.get("/blog/sitemap.xml"), "sitemap-artigos.xml")
        self.assertContains(self.client.get("/robots.txt"), "/blog/sitemap.xml")
        self.assertContains(self.client.get("/sitemap.xml"), "/blog/")

    def test_pending_and_future_are_not_public(self):
        article = self.article()
        self.assertEqual(self.client.get(article.get_absolute_url()).status_code, 404)
        article.status = "published"
        article.published_at = timezone.now() + timedelta(days=1)
        article.save()
        self.assertEqual(self.client.get(article.get_absolute_url()).status_code, 404)

    def test_html_and_json_injection_are_escaped(self):
        photo = self.photo()
        article = self.article(title='</script><script>alert("x")</script>',
                               body="<img src=x onerror=alert(1)>",
                               cover=photo, status="published", published_at=timezone.now())
        response = self.client.get(article.get_absolute_url())
        self.assertNotContains(response, '<script>alert("x")</script>')
        self.assertNotContains(response, "<img src=x onerror=alert(1)>")

    def test_dashboard_staff_permissions_and_admin_forms(self):
        self.assertEqual(self.client.get("/admin/blog/indicadores/").status_code, 302)
        user = get_user_model().objects.create_user("editor", password="test", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get("/admin/blog/indicadores/").status_code, 403)
        user.is_superuser = True
        user.save()
        response = self.client.get("/admin/blog/indicadores/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("noindex, nofollow", response["X-Robots-Tag"])
        self.assertContains(response, "Fontes cadastradas")
        self.assertEqual(self.client.get("/admin/blog/article/add/").status_code, 200)
        self.assertEqual(self.client.get("/admin/blog/photo/add/").status_code, 200)
        self.assertIn("withdraw", ArticleAdmin(Article, admin.site).get_actions(response.wsgi_request))

    def test_feed_deduplicates_and_ignores_html(self):
        source = self.item().source
        body = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>Feed</title><link>https://example.org/</link><description>News</description><item><title>Ping mundial: conectividade</title><link>https://example.org/novo</link><description>&lt;p&gt;Diagnostico DNS e ping.&lt;/p&gt;</description></item></channel></rss>"""
        run = EditorialRun.objects.create()
        with patch("blog.services.fetch", return_value=Response(source.feed_url, 200, {}, body, [], 0.1)):
            collect_source(source, run)
            collect_source(source, run)
        self.assertEqual(run.found, 1)
        item = NewsItem.objects.get(url="https://example.org/novo")
        self.assertNotIn("<p>", item.summary)
        self.assertGreaterEqual(item.score, 10)

    def test_generated_article_validation_duplicate_and_sources(self):
        item = self.item()
        article = create_article(item, self.payload())
        self.assertEqual(article.references, [item.url])
        self.assertTrue(article.generated)
        self.assertEqual(article.status, "pending")
        item.refresh_from_db()
        self.assertEqual(item.state, "used")
        with self.assertRaisesMessage(ValueError, "mesmo texto"):
            create_article(item, self.payload())
        with self.assertRaises(ValueError):
            create_article(item, {"error": "insuficiente"})

    def test_excessive_copy_is_rejected(self):
        item = self.item()
        item.summary = "Uma sequência exclusiva de contexto da fonte sobre rede e roteamento. " * 8
        payload = self.payload()
        payload["body"] = item.summary + payload["body"]
        with self.assertRaisesMessage(ValueError, "semelhante ao resumo"):
            create_article(item, payload)

    @override_settings(BLOG_OLLAMA_URL="http://169.254.169.254")
    @patch("blog.services.requests.post")
    def test_ollama_endpoint_cannot_use_cloud_metadata(self, post):
        with self.assertRaises(ValueError):
            ollama_generate(self.item())
        post.assert_not_called()

    @patch("blog.services.requests.post")
    def test_ollama_contract(self, post):
        response = post.return_value.__enter__.return_value
        response.status_code = 200
        response.iter_content.return_value = [json.dumps({"message": {"content": json.dumps(self.payload())}}).encode()]
        payload = ollama_generate(self.item())
        self.assertEqual(payload["title"], self.payload()["title"])
        self.assertFalse(post.call_args.kwargs["allow_redirects"])
        self.assertFalse(post.call_args.kwargs["json"]["stream"])

    @patch("blog.services.ollama_generate")
    def test_daily_idempotency_and_automatic_pipeline(self, generate):
        self.item()
        self.photo()
        generate.return_value = self.payload()
        with patch("blog.services.collect_source"):
            first = execute_run()
            second = execute_run()
        self.assertEqual(first.produced, 1)
        self.assertEqual(second.produced, 0)
        self.assertEqual(generate.call_count, 1)
        self.assertEqual(Article.objects.get().status, "scheduled")
        self.assertEqual(EditorialRun.objects.filter(generation_day=timezone.localdate()).count(), 1)

    @patch("blog.services.ollama_generate", side_effect=ValueError("private detail"))
    def test_errors_are_persistent_without_silent_success(self, generate):
        self.item()
        with patch("blog.services.collect_source"):
            run = execute_run()
        self.assertEqual(run.status, "partial")
        self.assertEqual(NewsItem.objects.get().state, "failed")
        self.assertEqual(run.events.filter(stage="generate", level="error").count(), 1)
        self.assertIsNotNone(run.finished_at)

    @patch("blog.services.collect_source", side_effect=ValueError("invalid feed"))
    def test_source_errors_persist(self, collect):
        self.item().delete()
        run = execute_run()
        self.assertEqual(run.status, "partial")
        self.assertTrue(run.events.filter(stage="collect", level="error").exists())

    @patch("blog.services.ollama_generate")
    def test_disabled_pipeline_has_no_external_calls(self, generate):
        self.config.enabled = False
        self.config.save()
        self.assertIsNone(execute_run())
        generate.assert_not_called()

    def test_tool_selection_uses_relevant_whole_words(self):
        self.assertEqual(recommended_tools("Ping e perda de pacotes")[0]["name"], "Ping mundial")
        self.assertEqual(recommended_tools("Planejamento IPv4 com CIDR")[0]["name"], "Calculadora CIDR")
        self.assertEqual(recommended_tools("shopping"), [])
