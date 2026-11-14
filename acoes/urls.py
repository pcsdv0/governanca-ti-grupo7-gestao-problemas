"""Rotas de Ações Corretivas (RF20, RF21)."""

from django.urls import path

from . import views

app_name = "acoes"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("problema/<int:problema_pk>/nova/", views.cadastrar, name="cadastrar"),
    path("<int:pk>/status/", views.alterar_status, name="alterar_status"),
]
