from decimal import Decimal
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from .optics import asymmetric_loss, fiber_loss


class OpticalPrimitivesTests(SimpleTestCase):
    def test_fiber_and_accessories_without_intermediate_rounding(self):
        self.assertEqual(fiber_loss('2.25', '.35', 2, '.3', 3, '.1', '.25'), Decimal('1.9375'))

    def test_theoretical_asymmetric_split(self):
        self.assertEqual(asymmetric_loss(10), Decimal(10))
        self.assertLess(abs(asymmetric_loss(90) - Decimal('0.457574905606751')), Decimal('1e-15'))

    def test_manufacturer_loss_replaces_theoretical_value(self):
        self.assertEqual(asymmetric_loss(10, '.2'), Decimal('10.2'))
        self.assertEqual(asymmetric_loss(10, '.2', '10.6'), Decimal('10.6'))

    def test_invalid_inputs(self):
        for value in ['NaN', 'Infinity', -1, 'invalid']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                fiber_loss(value, '.35')
        for value in [0, 100, -10]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                asymmetric_loss(value)
        with self.assertRaises(ValueError):
            fiber_loss(1, '.35', connectors='1.5')


@override_settings(ALLOWED_HOSTS=['testserver'])
class DesignerPageTests(SimpleTestCase):
    def test_public_mvp_does_not_need_database_or_login(self):
        response = self.client.get(reverse('ftth_designer:editor'))
        self.assertEqual(response.status_code, 200)
        for text in ['id="designer-canvas"', 'id="designer-properties"', 'ETAPA 1 / MVP VISUAL', '/static/ftth_designer/editor.js']:
            self.assertContains(response, text)
        self.assertContains(response, 'id="site-nav"', count=1)
        self.assertNotContains(response, 'OTIMIZAR REDE')

    def test_menu_sitemap_and_existing_simulator(self):
        for path in ['/', '/sitemap.xml', '/ferramentas/simulador-ftth/']:
            with self.subTest(path=path):
                self.assertContains(self.client.get(path), '/ferramentas/projetista-ftth/')
        self.assertContains(self.client.get('/ferramentas/simulador-ftth/'), 'id="ftth-canvas"')
