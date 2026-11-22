from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from contas.models import Perfil
from contas.permissoes import perfil_requerido, usuario_tem_perfil
from sistemas.models import Sistema

from .forms import FiltroIncidenteForm, IncidenteForm
from .models import Incidente
from .permissoes import pode_editar_incidente


@perfil_requerido(
    Perfil.SUPORTE, Perfil.DESENVOLVEDOR, Perfil.GESTOR_TI, Perfil.RESPONSAVEL_SISTEMA
)
@require_GET
def listar(request):
    incidentes = Incidente.objects.select_related("sistema", "registrado_por")
    sistemas = Sistema.objects.all()
    if not request.user.is_superuser and request.user.perfil == Perfil.RESPONSAVEL_SISTEMA:
        incidentes = incidentes.filter(sistema__responsavel=request.user)
        sistemas = sistemas.filter(responsavel=request.user)

    form = FiltroIncidenteForm(request.GET, sistemas=sistemas)
    if form.is_valid():
        dados = form.cleaned_data
        if dados["vinculo_problema"]:
            incidentes = incidentes.filter(problema__isnull=dados["vinculo_problema"] == "sem")
        if dados["sistema"]:
            incidentes = incidentes.filter(sistema=dados["sistema"])
        if dados["data_inicio"]:
            incidentes = incidentes.filter(data_ocorrencia__date__gte=dados["data_inicio"])
        if dados["data_fim"]:
            incidentes = incidentes.filter(data_ocorrencia__date__lte=dados["data_fim"])
    else:
        incidentes = incidentes.none()

    for incidente in incidentes:
        incidente.pode_editar = pode_editar_incidente(request.user, incidente)
    return render(
        request,
        "incidentes/lista.html",
        {
            "incidentes": incidentes,
            "form": form,
            "pode_cadastrar": usuario_tem_perfil(request.user, [Perfil.SUPORTE]),
        },
    )


@perfil_requerido(Perfil.SUPORTE)
@require_http_methods(["GET", "POST"])
def cadastrar(request):
    form = IncidenteForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            incidente = form.save(commit=False)
            incidente.registrado_por = request.user
            incidente.save()
        messages.success(request, "Incidente registrado com sucesso.")
        return redirect("incidentes:listar")
    return render(request, "incidentes/form.html", {"form": form, "titulo": "Registrar Incidente"})


@perfil_requerido(Perfil.SUPORTE, Perfil.GESTOR_TI)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def editar(request, pk):
    queryset = Incidente.objects.all()
    if request.method == "POST":
        queryset = queryset.select_for_update()
    incidente = get_object_or_404(queryset, pk=pk)
    if not pode_editar_incidente(request.user, incidente):
        raise PermissionDenied("Você não tem permissão para editar este incidente.")
    form = IncidenteForm(
        request.POST if request.method == "POST" else None,
        instance=incidente,
    )
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, "Incidente atualizado com sucesso.")
        return redirect("incidentes:listar")
    return render(request, "incidentes/form.html", {"form": form, "titulo": "Editar Incidente"})
