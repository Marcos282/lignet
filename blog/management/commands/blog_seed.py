from datetime import time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from blog.initial_articles import ARTICLES, CATEGORIES
from blog.models import Article, Category, EditorialRun, EditorialSettings, Keyword, PublicationSlot
from blog.services import event


class Command(BaseCommand):
    help = "Prepara os 20 guias originais iniciais, sem sobrescrever artigos ou publicar sem foto."

    @transaction.atomic
    def handle(self, **options):
        config = EditorialSettings.current()
        for value in [time(9), time(13), time(18)]:
            PublicationSlot.objects.get_or_create(time=value)
        categories = {}
        for slug, (name, topics) in CATEGORIES.items():
            categories[slug], _ = Category.objects.get_or_create(slug=slug, defaults={"name": name, "topics": topics})
        run = EditorialRun.objects.create()
        for title, category, excerpt, body, references in ARTICLES:
            slug = slugify(title)
            if Article.objects.filter(slug=slug).exists():
                continue
            article = Article(title=title, slug=slug, category=categories[category],
                              excerpt=excerpt, body=body, references=references)
            article.full_clean()
            article.save()
            for name in CATEGORIES[category][1].split(","):
                keyword, _ = Keyword.objects.get_or_create(name=name)
                article.keywords.add(keyword)
            run.produced += 1
            event(run, "seed", "Guia original inicial criado; aguardando foto para o fluxo automático.", article=article)
        run.status = "complete"
        run.finished_at = timezone.now()
        run.save()
        self.stdout.write(self.style.SUCCESS(
            f"{run.produced} guias criados. Automático: {config.automatic}. "
            "Envie fotos próprias, confira horários e habilite a rotina no painel."))
