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
    # F3: montar include("problemas.urls") após criar os templates do contrato
    # docs/integracao-problemas-f3.md. Evita expor páginas sem telas.
    # F3: montar também include("acoes.urls") e include("kedb.urls") após as telas.
    path("dashboard/", include("dashboard.urls")),
]
