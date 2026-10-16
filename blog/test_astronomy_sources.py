from io import StringIO
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from core.network import Response
from .astronomy_sources import SOURCES
from .models import Category, EditorialRun, Source, NewsItem
from .services import collect_source


class AstronomySourcesTests(TestCase):
    def test_registers_seven_real_rss_urls_without_authorization_assumption(self):
        errors = StringIO()
        with patch("blog.services.fetch") as fetch:
            call_command("blog_sources_astronomy", stdout=StringIO(), stderr=errors)
        fetch.assert_not_called()
        self.assertIn("Space.com: HTTP 403", errors.getvalue())
        self.assertIn("NASA Science: XML inválido", errors.getvalue())
        self.assertEqual(Source.objects.count(), 7)
        self.assertEqual(set(Source.objects.values_list("feed_url", flat=True)), {url for _, url, _ in SOURCES})
        for source in Source.objects.all():
            self.assertFalse(source.enabled)
            self.assertFalse(source.authorized)
            self.assertFalse(source.allow_auto_publish)
            source.full_clean()
        category = Category.objects.get(slug="astronomia")
        self.assertTrue(category.independent_topic)
        self.assertIn("exoplanet", category.topics)
        self.assertLessEqual(len(category.topics), 400)

    def test_rerun_preserves_admin_choices_and_existing_topics(self):
        call_command("blog_sources_astronomy", stdout=StringIO())
        source = Source.objects.first()
        source.enabled = source.authorized = source.allow_auto_publish = True
        source.priority = 2
        source.save()
        category = source.category
        category.independent_topic = False
        category.topics += ",observação"
        category.save()
        call_command("blog_sources_astronomy", stdout=StringIO())
        source.refresh_from_db()
        category.refresh_from_db()
        self.assertEqual(Source.objects.count(), 7)
        self.assertTrue(source.enabled and source.authorized and source.allow_auto_publish)
        self.assertEqual(source.priority, 2)
        self.assertFalse(category.independent_topic)
        self.assertIn("observação", category.topics)

    def test_can_register_sources_after_science_articles(self):
        call_command("blog_seed_science", stdout=StringIO())
        call_command("blog_sources_astronomy", stdout=StringIO(), stderr=StringIO())
        self.assertEqual(Source.objects.count(), 7)
        self.assertIn("exoplanets", Category.objects.get(slug="astronomia").topics)

    def test_overlong_category_terms_fail_explicitly_without_partial_registration(self):
        Category.objects.create(name="Astronomia", slug="astronomia", topics="x" * 400)
        with self.assertRaisesMessage(CommandError, "excedem o limite"):
            call_command("blog_sources_astronomy", stdout=StringIO())
        self.assertEqual(Source.objects.count(), 0)
        self.assertEqual(Category.objects.get(slug="astronomia").topics, "x" * 400)

    def test_english_title_is_selected_without_copying_news_images_or_full_content(self):
        call_command("blog_sources_astronomy", stdout=StringIO())
        source = Source.objects.get(name="NASA Science")
        body = b"""<?xml version="1.0"?><rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
        <channel><title>NASA</title><link>https://science.nasa.gov/</link><description>Feed</description>
        <item><title>New exoplanet observations</title><link>https://science.nasa.gov/exoplanets/test/</link>
        <description>&lt;p&gt;A telescope observes a distant planet.&lt;/p&gt;&lt;img src="https://example.org/photo.jpg"/&gt;</description>
        <content:encoded>FULL COPYRIGHTED ARTICLE SHOULD NOT BE STORED</content:encoded></item>
        <item><title>Office recruitment update</title><link>https://science.nasa.gov/office/</link>
        <description>A new administrative office announcement.</description></item>
        </channel></rss>"""
        with patch("blog.services.fetch", return_value=Response(source.feed_url, 200, {}, body, [], 0.1)) as fetch:
            collect_source(source, EditorialRun.objects.create())
        self.assertEqual(fetch.call_count, 1)
        item = NewsItem.objects.get(title="New exoplanet observations")
        self.assertGreaterEqual(item.score, 10)
        self.assertNotIn("<img", item.summary)
        self.assertNotIn("FULL COPYRIGHTED", item.summary)
        self.assertEqual(NewsItem.objects.get(title="Office recruitment update").score, 0)
