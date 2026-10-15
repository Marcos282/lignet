import json
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_safe
from .models import (Article, Category, EditorialEvent, EditorialRun,
                     EditorialSettings, NewsItem, Source)
from .tools import recommended_tools
from search_console.models import SearchConsoleConnection
from urllib.parse import urlsplit


@require_safe
def listing(request, category=None):
    config = EditorialSettings.objects.filter(pk=1).first()
    articles = Article.objects.public().select_related("category", "cover").prefetch_related("keywords")
    selected = get_object_or_404(Category, slug=category) if category else None
    if selected:
        articles = articles.filter(category=selected)
    page = Paginator(articles, config.page_size if config else 6).get_page(request.GET.get("page"))
    canonical = settings.SITE_URL + request.path
    if page.number > 1:
        canonical += "?page=" + str(page.number)
    return render(request, "blog/list.html", {
        "title": f"{selected.name} — Blog" if selected else "Blog de tecnologia e redes",
        "description": "Guias práticos de redes, endereçamento, imagens e SEO, com referências e ferramentas da Lignet Brasil.",
        "page": page, "selected": selected, "canonical": canonical,
        "categories": Category.objects.filter(article__in=Article.objects.public()).distinct(),
    })


@require_safe
def detail(request, slug):
    article = get_object_or_404(Article.objects.public().select_related("category", "cover").prefetch_related("keywords"), slug=slug)
    related = Article.objects.public().exclude(pk=article.pk).filter(
        Q(category=article.category) | Q(keywords__in=article.keywords.all())).annotate(
        shared=Count("keywords", filter=Q(keywords__in=article.keywords.all()), distinct=True)
    ).select_related("cover", "category").order_by("-shared", "-published_at").distinct()[:3]
    canonical = settings.SITE_URL + article.get_absolute_url()
    data = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": article.title, "description": article.excerpt, "mainEntityOfPage": canonical,
        "url": canonical, "datePublished": article.published_at.isoformat(),
        "dateModified": article.updated_at.isoformat(), "inLanguage": "pt-BR",
        "author": {"@type": "Organization", "name": "Redação Lignet Brasil"},
        "publisher": {"@type": "Organization", "name": "Lignet Brasil"},
        "keywords": [keyword.name for keyword in article.keywords.all()],
        "articleSection": article.category.name, "citation": article.references,
    }
    image_url = settings.SITE_URL + article.cover.image.url if article.cover else ""
    if image_url:
        data["image"] = image_url
    # Encode HTML delimiters before inserting JSON into a script element.
    schema = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return render(request, "blog/detail.html", {
        "title": article.title, "description": article.excerpt, "article": article,
        "related": related, "tools": recommended_tools(article.title + " " + article.body),
        "canonical": canonical, "schema": schema, "image_url": image_url,
    })


@staff_member_required
@permission_required("blog.view_article", raise_exception=True)
def overview(request):
    counts = {
        "Fontes cadastradas": Source.objects.count(),
        "Notícias encontradas": NewsItem.objects.count(),
        "Artigos produzidos": Article.objects.count(),
        "Publicações realizadas": EditorialEvent.objects.filter(stage="publish", level="info").count(),
        "Pendentes": Article.objects.filter(status__in=["draft", "pending"]).count(),
        "Erros registrados": EditorialEvent.objects.filter(level="error").count(),
    }
    response = render(request, "blog/overview.html", {
        "title": "Painel editorial", "counts": counts,
        "runs": Paginator(EditorialRun.objects.all(), 20).get_page(request.GET.get("page")),
        "events": Paginator(EditorialEvent.objects.select_related("article"), 20).get_page(request.GET.get("events")),
        "config": EditorialSettings.objects.filter(pk=1).first(),
        "connections": SearchConsoleConnection.objects.filter(
            owner=request.user, domain__status="verified", domain__hostname=urlsplit(settings.SITE_URL).hostname),
    })
    response["Cache-Control"] = "private, no-store"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response
