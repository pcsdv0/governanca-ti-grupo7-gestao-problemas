"""Rotas do RF17, aguardando as telas da F3 em config.urls."""

from django.urls import path

from . import views

app_name = "kedb"

urlpatterns = [
    path("problema/<int:problema_pk>/registrar/", views.registrar, name="registrar"),
]
