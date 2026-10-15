from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Article, Category


class ArticleSitemap(Sitemap):
    limit = 1000
    protocol = "https"

    def items(self):
        return Article.objects.public().order_by("pk")

    def lastmod(self, item):
        return item.updated_at


class CategorySitemap(Sitemap):
    limit = 1000
    protocol = "https"

    def items(self):
        return Category.objects.filter(article__in=Article.objects.public()).distinct().order_by("pk")

    def location(self, item):
        return reverse("blog:category", args=[item.slug])


sitemaps = {"artigos": ArticleSitemap, "categorias": CategorySitemap}
