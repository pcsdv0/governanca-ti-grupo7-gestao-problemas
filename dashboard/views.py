from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from acoes.models import AcaoCorretiva
from contas.models import Perfil
from incidentes.models import Incidente
from kedb.models import ErroConhecido
from problemas.services import problemas_visiveis


@login_required
def inicio(request):

    usuario = request.user

    # Consulta de problemas com as permissões
    # já definidas pelo backend do grupo.
    problemas = problemas_visiveis(usuario)

    # O responsável pelo sistema visualiza somente
    # os incidentes dos sistemas associados a ele.
    if usuario.perfil == Perfil.RESPONSAVEL_SISTEMA and not usuario.is_superuser:
        incidentes = Incidente.objects.filter(sistema__responsavel=usuario)
    else:
        incidentes = Incidente.objects.all()

    # Ações corretivas e erros conhecidos
    # limitados aos problemas visíveis.
    acoes = AcaoCorretiva.objects.filter(problema__in=problemas)

    erros_conhecidos = ErroConhecido.objects.filter(problema__in=problemas)

    # Indicadores numéricos
    total_incidentes = incidentes.count()
    total_problemas = problemas.count()
    total_acoes = acoes.count()
    total_erros_conhecidos = erros_conhecidos.count()

    # Incidentes por impacto
    incidentes_por_impacto = list(
        incidentes.values("impacto").annotate(total=Count("id")).order_by("impacto")
    )

    # Problemas por status
    problemas_por_status = list(
        problemas.values("status").annotate(total=Count("id")).order_by("status")
    )

    # Ações corretivas por status
    acoes_por_status = list(acoes.values("status").annotate(total=Count("id")).order_by("status"))

    contexto = {
        "total_incidentes": total_incidentes,
        "total_problemas": total_problemas,
        "total_acoes": total_acoes,
        "total_erros_conhecidos": total_erros_conhecidos,
        "incidentes_por_impacto": incidentes_por_impacto,
        "problemas_por_status": problemas_por_status,
        "acoes_por_status": acoes_por_status,
    }

    return render(request, "dashboard/inicio.html", contexto)
