from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from blog.astronomy_sources import ASTRONOMY_TERMS, FEED_WARNINGS, SOURCES
from blog.models import Category, Source


class Command(BaseCommand):
    help = "Cadastra sete feeds de astronomia para revisão dos termos, sem presumir autorização."

    @transaction.atomic
    def handle(self, **options):
        category, _ = Category.objects.get_or_create(
            slug="astronomia", defaults={"name": "Astronomia", "independent_topic": True})
        terms = [term.strip() for term in category.topics.split(",") if term.strip()]
        for term in ASTRONOMY_TERMS.split(","):
            if term not in terms:
                terms.append(term)
        combined = ",".join(terms)
        if len(combined) > Category._meta.get_field("topics").max_length:
            raise CommandError("Os termos de astronomia excedem o limite. Revise os termos da categoria.")
        category.topics = combined
        category.save(update_fields=["topics"])
        created = 0
        for name, url, priority in SOURCES:
            source, added = Source.objects.get_or_create(
                feed_url=url, defaults={"name": name, "category": category, "priority": priority,
                                        "enabled": False, "authorized": False, "allow_auto_publish": False})
            created += int(added)
            self.stdout.write(f"{source.name}: {source.feed_url}")
            if name in FEED_WARNINGS:
                self.stderr.write(self.style.WARNING(f"{name}: {FEED_WARNINGS[name]}"))
        self.stdout.write(self.style.SUCCESS(
            f"{created} fontes cadastradas. Configurações existentes preservadas. "
            "Revise os termos de cada editor no admin antes de marcar autorização e ativar coleta/publicação."))
