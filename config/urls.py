"""Rotas principais do projeto. Cada app publica as suas em <app>/urls.py."""

from django.contrib import admin
from django.urls import include, path

from contas.views import inicio

urlpatterns = [
    path("", inicio, name="inicio"),
    path("admin/", admin.site.urls),
    path("contas/", include("contas.urls")),
    path("sistemas/", include("sistemas.urls")),
    path("incidentes/", include("incidentes.urls")),
    path("problemas/", include("problemas.urls")),
    path("acoes/", include("acoes.urls")),
    path("kedb/", include("kedb.urls")),
    path("dashboard/", include("dashboard.urls")),
]
