from django.contrib import admin
from django.urls import path,include
from django.contrib.auth import views as auth_views
from core import views
from search_console import views as google
urlpatterns=[
    path('',include('globalping.urls')),
    path('',views.portal,name='home'),
    path('qr.js',views.legacy_asset,{'name':'qr.js'}),
    path('vendor/qrcode.js',views.legacy_asset,{'name':'vendor/qrcode.js'}),
    path('vendor/qrcode_UTF8.js',views.legacy_asset,{'name':'vendor/qrcode_UTF8.js'}),
    path('admin/operacao/',admin.site.admin_view(views.operations),name='operations'),
    path('admin/',admin.site.urls),
    path('conta/cadastro/',views.signup,name='signup'),
    path('conta/login/',auth_views.LoginView.as_view(),name='login'),
    path('conta/logout/',auth_views.LogoutView.as_view(),name='logout'),
    path('ferramentas/seo/',views.seo,name='seo'),
    path('relatorios/<uuid:pk>/',views.report,name='report'),
    path('painel/',views.dashboard,name='dashboard'),
    path('dominios/<int:pk>/<str:action>/',views.domain_action,name='domain_action'),
    path('integracoes/google/callback/',google.callback,name='google_callback'),
    path('integracoes/google/<int:pk>/conectar/',google.connect,name='google_connect'),
    path('integracoes/google/<int:pk>/atualizar/',google.refresh,name='google_refresh'),
    path('integracoes/google/<int:pk>/desconectar/',google.disconnect,name='google_disconnect'),
    path('sitemap.xml',views.portal_sitemap),path('robots.txt',views.portal_robots),
]
for kind in ('sitemap','robots-txt','indexnow','consultar-dns','calculadora-cidr'):
    urlpatterns.append(path('ferramentas/'+kind+'/',views.tool,{'kind':kind},name=kind))
admin.site.site_header='Lignet SEO — Administração'
admin.site.site_title='Lignet SEO'
admin.site.index_title='Operação, auditorias e integrações'
