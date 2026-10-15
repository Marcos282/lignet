from django.urls import path
from . import views

app_name='globalping'
urlpatterns=[
    path('api/globalping/medicoes/',views.start,name='start'),
    path('api/globalping/historico/',views.history,name='history'),
    path('api/globalping/medicoes/<uuid:pk>/',views.status,name='status'),
]
for slug in views.PAGES:
    urlpatterns.append(path('ferramentas/'+slug+'/',views.page,{'slug':slug},name=slug))
