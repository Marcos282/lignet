from datetime import time
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from core.models import Timestamped
from core.network import normalize_url


class Category(models.Model):
    name = models.CharField("Nome", max_length=80)
    slug = models.SlugField(unique=True)
    topics = models.CharField("Termos para selecionar pautas", max_length=400, blank=True,
                              help_text="Termos separados por vírgula.")
    independent_topic = models.BooleanField("Tema editorial independente das ferramentas", default=False)

    def __str__(self):
        return self.name


class Keyword(models.Model):
    name = models.CharField("Palavra-chave", max_length=60, unique=True)

    def __str__(self):
        return self.name


class Photo(Timestamped):
    title = models.CharField("Título", max_length=120)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    image = models.ImageField("Foto própria (JPG, PNG ou WebP; até 8 MB)", upload_to="blog/")
    alt = models.CharField("Descrição acessível da foto", max_length=240)
    credit = models.CharField("Autor / crédito", max_length=200)
    rights_confirmed = models.BooleanField("Confirmo que posso publicar esta foto", default=False)
    allow_automatic = models.BooleanField("Disponível para artigos automáticos desta categoria", default=True,
                                         help_text="Use fotos genéricas que não induzam a uma associação factual falsa.")
    generated = models.BooleanField("Ilustração gerada por IA", default=False, editable=False)
    model_name = models.CharField("Modelo local da imagem", max_length=200, blank=True, editable=False)

    def clean(self):
        super().clean()
        if not self.rights_confirmed:
            raise ValidationError("Confirme o direito de publicação da foto.")
        if not self.alt.strip() or not self.credit.strip():
            raise ValidationError("A foto precisa de descrição e crédito.")
        if self.image and not self.image._committed:
            from .photos import normalize_photo
            self.image = normalize_photo(self.image)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Source(Timestamped):
    name = models.CharField("Nome", max_length=100)
    feed_url = models.URLField("Feed RSS/Atom", max_length=2048, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    enabled = models.BooleanField("Ativa", default=True)
    authorized = models.BooleanField("Uso editorial autorizado", default=False,
                                    help_text="Confirme os termos do feed antes de habilitar a coleta.")
    allow_auto_publish = models.BooleanField("Permitir publicação automática desta fonte", default=True)
    priority = models.PositiveSmallIntegerField(default=5, validators=[MaxValueValidator(10)])
    last_collected_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        super().clean()
        self.feed_url = normalize_url(self.feed_url)
        if self.allow_auto_publish and not self.authorized:
            raise ValidationError("Publicação automática exige autorização de uso da fonte.")

    def __str__(self):
        return self.name


class EditorialSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    enabled = models.BooleanField("Habilitar rotina diária", default=False)
    automatic = models.BooleanField("Publicação automática", default=True)
    ai_enabled = models.BooleanField("Gerar novos textos com IA local", default=True,
                                    help_text="Desligar não pausa o Cron nem as publicações já agendadas.")
    images_enabled = models.BooleanField("Gerar capas com IA local", default=False,
                                        help_text="Exige ComfyUI local e checkpoint com licença conferida.")
    daily_limit = models.PositiveSmallIntegerField("Limite diário de artigos e publicações", default=3,
                                                  validators=[MinValueValidator(1), MaxValueValidator(20)])
    page_size = models.PositiveSmallIntegerField("Artigos por página", default=6,
                                                validators=[MinValueValidator(1), MaxValueValidator(50)])
    generation_time = models.TimeField("Gerar pautas a partir de", default=time(6))

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(id=1), name="blog_single_settings"),
            models.CheckConstraint(condition=models.Q(daily_limit__gte=1, daily_limit__lte=20), name="blog_daily_limit"),
            models.CheckConstraint(condition=models.Q(page_size__gte=1, page_size__lte=50), name="blog_page_size"),
        ]

    @classmethod
    def current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Configuração editorial"


class PublicationSlot(models.Model):
    time = models.TimeField("Horário local", unique=True)
    enabled = models.BooleanField("Ativo", default=True)

    class Meta:
        ordering = ["time"]

    def __str__(self):
        return str(self.time)


class NewsItem(Timestamped):
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    url = models.URLField(max_length=2048)
    fingerprint = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=240)
    summary = models.TextField()
    score = models.PositiveSmallIntegerField(default=0, db_index=True)
    state = models.CharField(max_length=12, choices=[("found", "Encontrada"), ("used", "Utilizada"),
                                                   ("failed", "Falhou"), ("ignored", "Ignorada")], default="found")

    def __str__(self):
        return self.title


class ArticleQuerySet(models.QuerySet):
    def public(self):
        return self.filter(status="published", published_at__lte=timezone.now())


class Article(Timestamped):
    title = models.CharField("Título", max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    excerpt = models.CharField("Descrição SEO / resumo", max_length=240)
    body = models.TextField("Texto", help_text="Texto simples. Separe parágrafos com uma linha em branco; HTML não é executado.")
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    cover = models.ForeignKey(Photo, verbose_name="Foto de capa", null=True, blank=True, on_delete=models.PROTECT)
    keywords = models.ManyToManyField(Keyword, blank=True, verbose_name="Palavras-chave")
    item = models.OneToOneField(NewsItem, null=True, blank=True, on_delete=models.PROTECT)
    status = models.CharField("Estado", max_length=12, default="pending", db_index=True, choices=[
        ("draft", "Rascunho"), ("pending", "Aguardando aprovação"),
        ("scheduled", "Aprovado / agendado"), ("published", "Publicado"), ("withdrawn", "Retirado manualmente")])
    scheduled_at = models.DateTimeField("Publicar a partir de", null=True, blank=True)
    approved_at = models.DateTimeField("Aprovação", null=True, blank=True, editable=False)
    published_at = models.DateTimeField("Publicado em", null=True, blank=True, editable=False)
    generated = models.BooleanField("Gerado com IA", default=False, editable=False)
    manual_approval = models.BooleanField(
        "Exigir minha aprovação manual", default=True,
        help_text="Marcado: o Cron não aprova este artigo. Artigos novos do painel usam esta opção por padrão.")
    image_prompt = models.TextField("Descrição da ilustração para IA", blank=True, max_length=2000)
    image_job = models.CharField(max_length=100, blank=True, editable=False)
    image_model = models.CharField(max_length=200, blank=True, editable=False)
    image_requested_at = models.DateTimeField(null=True, blank=True, editable=False)
    image_retry_at = models.DateTimeField(null=True, blank=True, editable=False)
    references = models.JSONField("Referências", default=list,
                                 help_text='Lista JSON de URLs públicas, por exemplo ["https://example.org/guia"].')
    objects = ArticleQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        permissions = [("approve_article", "Pode aprovar artigos para publicação")]

    def clean(self):
        super().clean()
        if not self.body.strip() or not self.excerpt.strip():
            raise ValidationError("Preencha o texto e a descrição.")
        if not isinstance(self.references, list) or not self.references or len(self.references) > 10:
            raise ValidationError({"references": "Informe de uma a dez URLs de referência."})
        try:
            self.references = [normalize_url(url) for url in self.references]
        except ValueError as exc:
            raise ValidationError({"references": str(exc)}) from exc
        if self.status in ("scheduled", "published") and not self.approved_at:
            raise ValidationError("Use a ação de aprovação do painel antes de agendar ou publicar.")
        if self.status in ("scheduled", "published") and (not self.cover or not self.cover.rights_confirmed):
            raise ValidationError({"cover": "Adicione uma foto própria com direitos confirmados antes de publicar."})

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("blog:detail", args=[self.slug])

    def __str__(self):
        return self.title


class EditorialRun(models.Model):
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True)
    generation_day = models.DateField(null=True, blank=True, unique=True)
    status = models.CharField(max_length=16, default="running",
                             choices=[("running", "Em execução"), ("complete", "Concluída"),
                                      ("partial", "Com erros"), ("failed", "Falhou")])
    found = models.PositiveIntegerField(default=0)
    produced = models.PositiveIntegerField(default=0)
    published = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-started_at"]


class EditorialEvent(models.Model):
    run = models.ForeignKey(EditorialRun, null=True, blank=True, on_delete=models.SET_NULL, related_name="events")
    article = models.ForeignKey(Article, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    stage = models.CharField(max_length=32)
    level = models.CharField(max_length=10, choices=[("info", "Informação"), ("error", "Erro")])
    message = models.CharField(max_length=500)

    class Meta:
        ordering = ["-created_at"]
