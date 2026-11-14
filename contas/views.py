from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import UsuarioCriarForm, UsuarioEditarForm
from .models import Perfil, Usuario
from .permissoes import perfil_requerido


@login_required
def inicio(request):
    """Página inicial: só para usuários logados, com atalhos conforme o perfil."""
    return render(request, "inicio.html")


@perfil_requerido(Perfil.GESTOR_TI)
@require_GET
def usuarios(request):
    """RF02: lista de Usuários com o perfil de cada um."""
    return render(
        request,
        "contas/lista.html",
        {"usuarios": Usuario.objects.order_by("perfil", "first_name", "username")},
    )


@perfil_requerido(Perfil.GESTOR_TI)
@require_http_methods(["GET", "POST"])
def cadastrar_usuario(request):
    """RF02: cadastro de Usuário com atribuição de perfil."""
    form = UsuarioCriarForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Usuário cadastrado com sucesso.")
        return redirect("contas:usuarios")
    return render(request, "contas/form.html", {"form": form, "titulo": "Cadastrar Usuário"})


@perfil_requerido(Perfil.GESTOR_TI)
@require_http_methods(["GET", "POST"])
def editar_usuario(request, pk):
    """RF02: edição de dados, perfil e situação (ativo/inativo). Não há exclusão."""
    usuario = get_object_or_404(Usuario, pk=pk)
    form = UsuarioEditarForm(request.POST if request.method == "POST" else None, instance=usuario)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Usuário atualizado com sucesso.")
        return redirect("contas:usuarios")
    return render(request, "contas/form.html", {"form": form, "titulo": "Editar Usuário"})
