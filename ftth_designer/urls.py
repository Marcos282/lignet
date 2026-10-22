from django.urls import path
from . import views

app_name = 'ftth_designer'
urlpatterns = [path('ferramentas/projetista-ftth/', views.editor, name='editor')]
