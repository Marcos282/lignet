from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from blog.models import Article, Category, EditorialRun, Keyword
from blog.science_articles import ARTICLES, CATEGORIES
from blog.services import event


class Command(BaseCommand):
    help = "Cria dez artigos originais de astronomia, utopia e IA, com prompts de capa local."

    @transaction.atomic
    def handle(self, **options):
        categories = {}
        for slug, (name, terms) in CATEGORIES.items():
            category, created = Category.objects.get_or_create(
                slug=slug, defaults={"name": name, "topics": terms, "independent_topic": True})
            if not category.independent_topic:
                category.independent_topic = True
                category.save(update_fields=["independent_topic"])
            categories[slug] = category
        run = EditorialRun.objects.create()
        for title, category, excerpt, body, references, prompt in ARTICLES:
            slug = slugify(title)
            if Article.objects.filter(slug=slug).exists():
                continue
            article = Article(title=title, slug=slug, category=categories[category], excerpt=excerpt,
                              body=body, references=references, generated=True, manual_approval=False,
                              image_prompt=prompt)
            article.full_clean()
            article.save()
            for term in CATEGORIES[category][1].split(",")[:6]:
                keyword, _ = Keyword.objects.get_or_create(name=term)
                article.keywords.add(keyword)
            event(run, "seed_science", "Artigo original preparado com auxílio de IA; capa local ainda pendente.", article=article)
            run.produced += 1
        run.status = "complete"
        run.finished_at = timezone.now()
        run.save()
        self.stdout.write(self.style.SUCCESS(
            f"{run.produced} artigos criados. Capas NÃO geradas por este comando. "
            "Configure ComfyUI/modelo local e habilite a geração de capas; sem capa válida não há publicação."))
