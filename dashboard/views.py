from django.shortcuts import render
from django.views.decorators.http import require_GET

from contas.models import Perfil
from contas.permissoes import perfil_requerido

from .services import indicadores


@perfil_requerido(Perfil.GESTOR_TI)
@require_GET
def painel(request):
    return render(request, "dashboard/painel.html", indicadores(usuario=request.user))
