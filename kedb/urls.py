from django.urls import path

from . import views

app_name = "kedb"

urlpatterns = [
    path("", views.pesquisar, name="pesquisar"),
    path("problema/<int:problema_pk>/registrar/", views.registrar, name="registrar"),
]
