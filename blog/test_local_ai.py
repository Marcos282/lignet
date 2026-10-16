import tempfile
from datetime import time, timedelta
from io import BytesIO, StringIO
from unittest.mock import patch

import requests
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from .local_images import endpoint, local_request, receive_image, submit_image
from .models import Article, Category, EditorialRun, EditorialSettings, PublicationSlot
from .services import execute_run, generate_theme, process_images


@override_settings(BLOG_COMFY_URL="http://127.0.0.1:8188",
                   BLOG_IMAGE_CHECKPOINT="licensed-model.safetensors", BLOG_IMAGE_LICENSE_CONFIRMED=True)
class LocalAITests(TestCase):
    def setUp(self):
        self.storage = tempfile.TemporaryDirectory()
        self.media = override_settings(MEDIA_ROOT=self.storage.name)
        self.media.enable()
        self.addCleanup(self.storage.cleanup)
        self.addCleanup(self.media.disable)
        call_command("blog_seed_science", stdout=StringIO())
        self.article = Article.objects.filter(category__slug="astronomia").order_by("created_at", "pk").first()
        self.config = EditorialSettings.current()
        self.config.enabled = True
        self.config.generation_time = time(0)
        self.config.images_enabled = True
        self.config.save()

    @staticmethod
    def image_bytes():
        output = BytesIO()
        Image.new("RGB", (768, 512), "navy").save(output, format="PNG")
        return output.getvalue()

    def completed_image(self):
        self.article.image_job = "12345678-abcd"
        self.article.image_model = "original-model.safetensors"
        self.article.image_requested_at = timezone.now()
        self.article.save()
        history = {self.article.image_job: {"status": {"completed": True, "status_str": "success"},
                                          "outputs": {"7": {"images": [
                                              {"filename": "lignet.png", "subfolder": "", "type": "output"}]}}}}
        with patch("blog.local_images.local_request", side_effect=[history, self.image_bytes()]):
            self.assertTrue(receive_image(self.article))
        return self.article.cover

    def schedule_due(self):
        cover = self.completed_image()
        self.article.status = "scheduled"
        self.article.approved_at = timezone.now()
        self.article.scheduled_at = timezone.now() - timedelta(minutes=1)
        self.article.save()
        return cover

    def test_seed_exactly_ten_complete_and_idempotent(self):
        self.assertEqual(Article.objects.count(), 10)
        self.assertEqual(Article.objects.filter(category__slug="astronomia").count(), 4)
        self.assertEqual(Article.objects.filter(category__slug="utopia").count(), 3)
        self.assertEqual(Article.objects.filter(category__slug="inteligencia-artificial").count(), 3)
        for article in Article.objects.all():
            article.full_clean()
            self.assertGreaterEqual(len(article.body), 1200)
            self.assertGreaterEqual(len(article.excerpt), 70)
            self.assertTrue(article.image_prompt)
            self.assertIsNone(article.cover)
            self.assertEqual(article.status, "pending")
            self.assertFalse(article.manual_approval)
            self.assertTrue(article.references)
        self.article.status = "withdrawn"
        self.article.body = "Texto editado manualmente."
        self.article.save()
        call_command("blog_seed_science", stdout=StringIO())
        self.article.refresh_from_db()
        self.assertEqual(Article.objects.count(), 10)
        self.assertEqual(self.article.status, "withdrawn")
        self.assertEqual(self.article.body, "Texto editado manualmente.")
        self.assertEqual(Category.objects.filter(independent_topic=True).count(), 3)

    def test_model_disabled_does_not_pause_due_publication(self):
        self.schedule_due()
        self.config.ai_enabled = False
        self.config.images_enabled = False
        self.config.save()
        with patch("blog.services.ollama_text") as text, patch("blog.local_images.local_request") as images:
            run = execute_run()
        text.assert_not_called()
        images.assert_not_called()
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, "published")
        self.assertEqual(run.published, 1)
        self.assertIsNone(run.generation_day)

    def test_text_and_image_outages_preserve_publication(self):
        self.schedule_due()
        with patch("blog.services.ollama_text", side_effect=requests.ConnectionError), \
                patch("blog.local_images.local_request", side_effect=requests.ConnectionError):
            run = execute_run()
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, "published")
        self.assertEqual(run.published, 1)
        self.assertEqual(run.status, "partial")
        self.assertTrue(run.events.filter(stage="image", level="error").exists())
        self.assertTrue(run.events.filter(stage="generate", level="error").exists())
        self.assertEqual(Article.objects.filter(status="pending").count(), 9)

    def test_inactive_routine_still_explicitly_stops_all_work(self):
        self.config.enabled = False
        self.config.save()
        self.assertIsNone(execute_run())

    @patch("blog.local_images.local_request")
    def test_submit_fixed_workflow_and_nonblocking_poll(self, request):
        request.return_value = {"prompt_id": "12345678-abcd"}
        submit_image(self.article)
        graph = request.call_args.kwargs["payload"]["prompt"]
        self.assertEqual(graph["4"]["inputs"]["batch_size"], 1)
        self.assertEqual(graph["1"]["inputs"]["ckpt_name"], "licensed-model.safetensors")
        self.assertEqual(self.article.image_job, "12345678-abcd")
        self.assertEqual(self.article.image_model, "licensed-model.safetensors")
        request.return_value = {}
        self.assertFalse(receive_image(self.article))
        self.assertIsNone(self.article.cover)
        self.assertEqual(request.call_args.args[1], "/history/12345678-abcd")

    def test_real_image_reencoding_provenance_and_public_caption(self):
        photo = self.completed_image()
        self.assertTrue(photo.generated)
        self.assertTrue(photo.rights_confirmed)
        self.assertFalse(photo.allow_automatic)
        self.assertEqual(photo.model_name, "original-model.safetensors")
        self.assertTrue(photo.image.name.endswith(".jpg"))
        self.assertEqual(self.article.image_job, "")
        self.article.status = "published"
        self.article.approved_at = timezone.now()
        self.article.published_at = timezone.now()
        self.article.save()
        response = self.client.get(self.article.get_absolute_url())
        self.assertContains(response, "Ilustração gerada por IA, não uma fotografia")
        self.assertNotContains(response, "Foto:")

    @patch("blog.local_images.local_request")
    def test_invalid_image_never_attaches_cover(self, request):
        self.config.daily_limit = 1
        self.article.image_job = "12345678-abcd"
        self.article.image_requested_at = timezone.now()
        self.article.save()
        request.side_effect = [
            {self.article.image_job: {"status": {"completed": True}, "outputs": {
                "7": {"images": [{"filename": "x.png", "type": "output"}]}}}}, b"not an image"]
        run = EditorialRun.objects.create()
        process_images(self.config, run)
        self.article.refresh_from_db()
        self.assertIsNone(self.article.cover)
        self.assertTrue(self.article.image_retry_at > timezone.now())
        self.assertEqual(self.article.status, "pending")

    @patch("blog.local_images.local_request", return_value={})
    def test_missing_job_is_not_automatically_resubmitted(self, request):
        self.article.image_job = "12345678-abcd"
        self.article.image_requested_at = timezone.now() - timedelta(hours=3)
        self.article.save()
        self.config.daily_limit = 1
        run = EditorialRun.objects.create()
        process_images(self.config, run)
        self.article.refresh_from_db()
        self.assertEqual(self.article.image_job, "12345678-abcd")
        self.assertIsNotNone(self.article.image_retry_at)
        self.assertTrue(run.events.filter(level="error").exists())
        self.assertEqual(request.call_count, 1)

    @patch("blog.local_images.requests.Session")
    def test_loopback_only_license_and_checkpoint_guards(self, session):
        for url in ["https://127.0.0.1:8188", "http://example.com", "http://127.0.0.1/private",
                    "http://user:pass@localhost:8188", "http://localhost:8188?x=1"]:
            with self.subTest(url=url), override_settings(BLOG_COMFY_URL=url):
                with self.assertRaises(ValueError):
                    endpoint()
        with override_settings(BLOG_IMAGE_LICENSE_CONFIRMED=False):
            with self.assertRaises(ValueError):
                endpoint()
        with override_settings(BLOG_IMAGE_CHECKPOINT="../secret"):
            with self.assertRaises(ValueError):
                submit_image(self.article)
        session.assert_not_called()

    @patch("blog.local_images.requests.Session")
    def test_http_limits_and_proxy_isolation(self, session_factory):
        session = session_factory.return_value.__enter__.return_value
        response = session.request.return_value.__enter__.return_value
        response.status_code = 200
        response.iter_content.return_value = [b'{"prompt_id":"12345678-abcd"}']
        self.assertEqual(local_request("POST", "/prompt")["prompt_id"], "12345678-abcd")
        self.assertFalse(session.trust_env)
        self.assertFalse(session.request.call_args.kwargs["allow_redirects"])
        response.iter_content.return_value = [b"x" * (1024 * 1024 + 1)]
        with self.assertRaisesMessage(ValueError, "limite"):
            local_request("GET", "/history/job")
        response.status_code = 302
        with self.assertRaisesMessage(ValueError, "302"):
            local_request("GET", "/history/job")

    @patch("blog.services.ollama_text")
    def test_new_theme_uses_local_model_without_paid_api_or_feed(self, text):
        text.return_value = {
            "title": "Espectros estelares e as perguntas que fazemos à luz",
            "excerpt": "Entenda como instrumentos separam a luz e por que observar um espectro exige interpretação e limites.",
            "body": ("O espectro organiza a radiação observada por comprimento de onda. "
                     "Um instrumento precisa de calibração e os dados devem ser interpretados com cuidado.\n\n") * 12}
        run = EditorialRun.objects.create()
        self.assertTrue(generate_theme(run, 0))
        self.assertEqual(run.produced, 1)
        article = Article.objects.latest("pk")
        self.assertIsNone(article.item)
        self.assertTrue(article.generated)
        self.assertTrue(article.image_prompt)
        self.assertTrue(article.references)
        self.assertIn("Não copie", text.call_args.args[1])
        self.assertIn("títulos", text.call_args.args[1])

    @patch("blog.services.ollama_text")
    def test_daily_generation_fills_exact_limit_without_feeds_and_is_not_repeated(self, text):
        text.side_effect = [
            {"title": title, "excerpt": "Uma explicação educativa original sobre o tema, com limites e contexto para uma leitura cuidadosa.",
             "body": (body + "\n\n") * 30}
            for title, body in [
                ("Espectros estelares e as perguntas que fazemos à luz", "A luz contém informações que precisam ser interpretadas com instrumentos calibrados."),
                ("Conjuntos de treinamento e avaliação de algoritmos", "A avaliação precisa ser separada dos dados usados durante o treinamento de um modelo."),
                ("Espaços compartilhados e participação nas decisões", "Um cenário filosófico pode comparar modos distintos de decidir sobre o uso de áreas comuns."),
            ]]
        self.config.images_enabled = False
        self.config.save()
        run = execute_run()
        execute_run()
        self.assertEqual(run.produced, 3)
        self.assertEqual(Article.objects.count(), 13)
        self.assertEqual(text.call_count, 3)
        self.assertEqual(EditorialRun.objects.filter(generation_day=timezone.localdate()).count(), 1)

    @patch("blog.local_images.local_request")
    def test_completed_cover_is_automatically_scheduled(self, request):
        self.config.ai_enabled = False
        self.config.daily_limit = 1
        self.config.save()
        PublicationSlot.objects.create(time=time(9))
        self.article.image_job = "12345678-abcd"
        self.article.image_model = "licensed-model.safetensors"
        self.article.image_requested_at = timezone.now()
        self.article.save()
        request.side_effect = [
            {self.article.image_job: {"status": {"completed": True}, "outputs": {
                "7": {"images": [{"filename": "x.png", "type": "output"}]}}}}, self.image_bytes()]
        run = execute_run()
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, "scheduled")
        self.assertTrue(self.article.cover.generated)
        self.assertIsNotNone(self.article.approved_at)
        self.assertEqual(run.status, "complete")
