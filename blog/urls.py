from django.contrib.sitemaps import views as sitemap_views
from django.urls import path
from . import views
from .sitemaps import sitemaps

app_name = "blog"
urlpatterns = [
    path("", views.listing, name="list"),
    path("categoria/<slug:category>/", views.listing, name="category"),
    path("artigos/<slug:slug>/", views.detail, name="detail"),
    path("sitemap.xml", sitemap_views.index, {"sitemaps": sitemaps, "sitemap_url_name": "blog:sitemap-section",
                                            "template_name": "blog/sitemap-index.xml"}, name="sitemap"),
    path("sitemap-<section>.xml", sitemap_views.sitemap, {"sitemaps": sitemaps,
                                                      "template_name": "blog/sitemap.xml"}, name="sitemap-section"),
]
