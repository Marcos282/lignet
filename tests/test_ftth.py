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
