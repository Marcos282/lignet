from django.test import SimpleTestCase, override_settings
from django.urls import reverse

@override_settings(ALLOWED_HOSTS=['testserver'])
class FtthPageTests(SimpleTestCase):
    def test_public_editor_without_database_or_login(self):
        response = self.client.get(reverse('simulador-ftth'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="ftth-canvas"')
        self.assertContains(response, 'type="module"')
        self.assertContains(response, 'id="site-fiber"', count=1)
        self.assertContains(response, 'id="site-nav"', count=1)
        self.assertContains(response, '/static/ftth/editor.js')

    def test_simulator_discoverable_in_sitemap_and_home_navigation(self):
        for path in ('/', '/sitemap.xml', '/ferramentas/calculadora-cidr/'):
            with self.subTest(path=path):
                self.assertContains(self.client.get(path), '/ferramentas/simulador-ftth/')

    def test_static_homepage_has_standalone_navigation(self):
        from django.conf import settings
        from django.core.management import call_command
        from io import StringIO
        html = (settings.BASE_DIR / 'index.html').read_text(encoding='utf-8')
        self.assertEqual(html.count('id="site-nav"'), 1)
        self.assertIn('/ferramentas/simulador-ftth/', html)
        self.assertIn('<!-- SITE_NAV_STYLE_START -->', html)
        self.assertGreater(html.index('<!-- SITE_NAV_SCRIPT_START -->'), html.index('</main>'))
        self.assertNotIn('<!-- SITE_NAVIGATION -->', html)
        call_command('build_portal_navigation', check=True, stdout=StringIO())

    def test_django_homepage_renders_only_one_navigation(self):
        from types import SimpleNamespace
        from django.test import RequestFactory
        from core.views import portal
        request = RequestFactory().get('/')
        request.user = SimpleNamespace(is_authenticated=True)
        response = portal(request)
        self.assertContains(response, 'id="site-nav"', count=1)
        self.assertContains(response, 'Meu painel ↗')
        self.assertNotContains(response, 'href="/conta/login/">Entrar')
