from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from contas.models import Perfil
from contas.permissoes import perfil_requerido

from .forms import SistemaForm
from .models import Sistema


@perfil_requerido(Perfil.GESTOR_TI)
@require_GET
def listar(request):
    sistemas = Sistema.objects.select_related("responsavel")
    return render(request, "sistemas/lista.html", {"sistemas": sistemas})


@perfil_requerido(Perfil.GESTOR_TI)
@require_http_methods(["GET", "POST"])
def cadastrar(request):
    form = SistemaForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sistema cadastrado com sucesso.")
        return redirect("sistemas:listar")
    return render(request, "sistemas/form.html", {"form": form, "titulo": "Cadastrar Sistema"})


@perfil_requerido(Perfil.GESTOR_TI)
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    sistema = get_object_or_404(Sistema, pk=pk)
    form = SistemaForm(
        request.POST if request.method == "POST" else None,
        instance=sistema,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sistema atualizado com sucesso.")
        return redirect("sistemas:listar")
    return render(request, "sistemas/form.html", {"form": form, "titulo": "Editar Sistema"})
