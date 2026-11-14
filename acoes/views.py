from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from contas.models import Perfil, Usuario
from contas.permissoes import perfil_requerido
from problemas.forms import adicionar_erros
from problemas.models import Problema

from .constantes import StatusAcaoCorretiva
from .forms import AcaoCorretivaForm, AlterarStatusAcaoForm
from .models import AcaoCorretiva
from .services import alterar_status_acao, criar_acao


@perfil_requerido(*Perfil.values)
@require_GET
def listar(request):
    """Consulta das Ações Corretivas, com filtro de status e responsável."""
    acoes = AcaoCorretiva.objects.select_related("problema", "responsavel").order_by("prazo", "pk")
    if not request.user.is_superuser and request.user.perfil == Perfil.RESPONSAVEL_SISTEMA:
        acoes = acoes.filter(problema__sistema__responsavel=request.user)
    status = request.GET.get("status", "")
    responsavel = request.GET.get("responsavel", "")
    if status in StatusAcaoCorretiva.values:
        acoes = acoes.filter(status=status)
    if responsavel.isdigit():
        acoes = acoes.filter(responsavel_id=int(responsavel))
    return render(
        request,
        "acoes/lista.html",
        {
            "acoes": acoes,
            "status_choices": StatusAcaoCorretiva.choices,
            "responsaveis": Usuario.objects.filter(perfil=Perfil.DESENVOLVEDOR).order_by(
                "first_name", "username"
            ),
            "filtro": {"status": status, "responsavel": responsavel},
        },
    )


@perfil_requerido(Perfil.DESENVOLVEDOR, Perfil.GESTOR_TI)
@require_http_methods(["GET", "POST"])
def cadastrar(request, problema_pk):
    problema = get_object_or_404(Problema, pk=problema_pk)
    form = AcaoCorretivaForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            criar_acao(
                usuario=request.user,
                problema_id=problema.pk,
                descricao=form.cleaned_data["descricao"],
                prazo=form.cleaned_data["prazo"],
                responsavel_id=form.cleaned_data["responsavel"].pk,
            )
        except Problema.DoesNotExist as exc:
            raise Http404("Problema não encontrado.") from exc
        except ValidationError as exc:
            adicionar_erros(form, exc)
        else:
            messages.success(request, "AçãoCorretiva criada com sucesso.")
            return redirect("problemas:detalhe", pk=problema.pk)
    return render(
        request,
        "acoes/form.html",
        {
            "form": form,
            "problema": problema,
            "titulo": "Criar AçãoCorretiva",
        },
    )


@perfil_requerido(Perfil.DESENVOLVEDOR)
@require_http_methods(["GET", "POST"])
def alterar_status(request, pk):
    acao = get_object_or_404(AcaoCorretiva.objects.select_related("problema"), pk=pk)
    form = AlterarStatusAcaoForm(
        request.POST if request.method == "POST" else None,
        acao=acao,
    )
    if request.method == "POST" and form.is_valid():
        try:
            alterar_status_acao(usuario=request.user, acao_id=acao.pk, **form.cleaned_data)
        except (AcaoCorretiva.DoesNotExist, Problema.DoesNotExist) as exc:
            raise Http404("AçãoCorretiva não encontrada.") from exc
        except ValidationError as exc:
            adicionar_erros(form, exc)
        else:
            messages.success(request, "Status da ação atualizado com sucesso.")
            return redirect("problemas:detalhe", pk=acao.problema_id)
    return render(
        request,
        "acoes/form.html",
        {
            "form": form,
            "problema": acao.problema,
            "acao": acao,
            "titulo": "Alterar status da AçãoCorretiva",
        },
    )
