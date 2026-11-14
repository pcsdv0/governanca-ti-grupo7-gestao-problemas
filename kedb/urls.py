"""Rotas do RF17 (registro de ErroConhecido)."""

from django.urls import path

from . import views

app_name = "kedb"

urlpatterns = [
    path("problema/<int:problema_pk>/registrar/", views.registrar, name="registrar"),
]
