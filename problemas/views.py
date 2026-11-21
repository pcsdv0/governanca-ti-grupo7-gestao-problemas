from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from acoes.models import AcaoCorretiva
from contas.models import Perfil
from contas.permissoes import perfil_requerido
from kedb.models import ErroConhecido

from . import services
from .forms import (
    AbrirProblemaForm,
    AlterarStatusForm,
    AtribuirProblemaForm,
    CausaRaizForm,
    VincularIncidentesForm,
    adicionar_erros,
)
from .models import CausaRaiz, Problema


@perfil_requerido(*Perfil.values)
@require_GET
def listar(request):
    return render(
        request,
        "problemas/lista.html",
        {
            "problemas": services.problemas_visiveis(request.user),
        },
    )


@perfil_requerido(*Perfil.values)
@require_GET
def detalhe(request, pk):
    problema = get_object_or_404(services.problemas_visiveis(request.user), pk=pk)
    historicos = {
        "Problema": problema.history.select_related("history_user"),
        "CausaRaiz": CausaRaiz.history.filter(problema_id=pk).select_related("history_user"),
        "ErroConhecido": ErroConhecido.history.filter(problema_id=pk).select_related(
            "history_user"
        ),
        "AçãoCorretiva": AcaoCorretiva.history.filter(problema_id=pk).select_related(
            "history_user"
        ),
    }
    linha_do_tempo = sorted(
        (
            {
                "entidade": entidade,
                "registro": registro,
                "data": registro.history_date,
                "usuario": registro.history_user,
            }
            for entidade, registros in historicos.items()
            for registro in registros
        ),
        key=lambda evento: (evento["data"], evento["entidade"], evento["registro"].history_id),
    )
    return render(
        request,
        "problemas/detalhe.html",
        {
            "problema": problema,
            "incidentes": problema.incidentes.select_related("registrado_por"),
            "historico_status": problema.historico_status.select_related("usuario"),
            "historico": historicos["Problema"],
            "causa_raiz": CausaRaiz.objects.filter(problema=problema).first(),
            "erro_conhecido": ErroConhecido.objects.filter(problema=problema).first(),
            "acoes": problema.acoes_corretivas.select_related("responsavel"),
            "historico_causa_raiz": historicos["CausaRaiz"],
            "historico_erro_conhecido": historicos["ErroConhecido"],
            "historico_acoes": historicos["AçãoCorretiva"],
            "linha_do_tempo": linha_do_tempo,
        },
    )


@perfil_requerido(Perfil.SUPORTE)
@require_http_methods(["GET", "POST"])
def cadastrar(request):
    form = AbrirProblemaForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            problema = services.abrir_problema(
                usuario=request.user,
                titulo=form.cleaned_data["titulo"],
                descricao=form.cleaned_data["descricao"],
                incidentes_ids=[incidente.pk for incidente in form.cleaned_data["incidentes"]],
            )
        except ValidationError as erro:
            adicionar_erros(form, erro)
        else:
            messages.success(request, "Problema registrado com sucesso.")
            return redirect("problemas:detalhe", pk=problema.pk)
    return render(request, "problemas/form.html", {"form": form, "titulo": "Registrar Problema"})


def _alterar(request, pk, classe_form, operacao, titulo):
    problema = get_object_or_404(Problema, pk=pk)
    kwargs = (
        {"problema": problema}
        if classe_form != AtribuirProblemaForm
        else {
            "initial": {"responsavel": problema.responsavel_id, "prioridade": problema.prioridade}
        }
    )
    form = classe_form(request.POST if request.method == "POST" else None, **kwargs)
    if request.method == "POST" and form.is_valid():
        dados = form.cleaned_data.copy()
        if "incidentes" in dados:
            dados["incidentes_ids"] = [incidente.pk for incidente in dados.pop("incidentes")]
        if "responsavel" in dados:
            dados["responsavel_id"] = dados.pop("responsavel").pk
        try:
            operacao(usuario=request.user, problema_id=pk, **dados)
        except Problema.DoesNotExist as erro:
            raise Http404("Problema não encontrado.") from erro
        except ValidationError as erro:
            adicionar_erros(form, erro)
        else:
            messages.success(request, "Problema atualizado com sucesso.")
            return redirect("problemas:detalhe", pk=pk)
    return render(
        request,
        "problemas/form.html",
        {
            "form": form,
            "problema": problema,
            "titulo": titulo,
        },
    )


@perfil_requerido(Perfil.SUPORTE)
@require_http_methods(["GET", "POST"])
def vincular(request, pk):
    return _alterar(
        request,
        pk,
        VincularIncidentesForm,
        services.vincular_incidentes,
        "Vincular Incidentes",
    )


@perfil_requerido(Perfil.GESTOR_TI)
@require_http_methods(["GET", "POST"])
def atribuir(request, pk):
    return _alterar(
        request,
        pk,
        AtribuirProblemaForm,
        services.atribuir_responsavel_prioridade,
        "Atribuir responsável e prioridade",
    )


@perfil_requerido(Perfil.DESENVOLVEDOR, Perfil.GESTOR_TI)
@require_http_methods(["GET", "POST"])
def alterar_status(request, pk):
    return _alterar(
        request,
        pk,
        AlterarStatusForm,
        services.alterar_status,
        "Alterar status",
    )


@perfil_requerido(Perfil.DESENVOLVEDOR)
@require_http_methods(["GET", "POST"])
def registrar_causa_raiz(request, pk):
    problema = get_object_or_404(Problema, pk=pk)
    causa = CausaRaiz.objects.filter(problema=problema).first()
    initial = (
        {
            "descricao": causa.descricao,
            "analise_5_porques": causa.analise_5_porques,
        }
        if causa
        else None
    )
    form = CausaRaizForm(
        request.POST if request.method == "POST" else None,
        initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        try:
            services.registrar_causa_raiz(
                usuario=request.user,
                problema_id=problema.pk,
                **form.cleaned_data,
            )
        except Problema.DoesNotExist as exc:
            raise Http404("Problema não encontrado.") from exc
        except ValidationError as exc:
            adicionar_erros(form, exc)
        else:
            messages.success(request, "CausaRaiz salva com sucesso.")
            return redirect("problemas:detalhe", pk=problema.pk)
    return render(
        request,
        "problemas/form.html",
        {
            "form": form,
            "problema": problema,
            "causa_raiz": causa,
            "titulo": "Registrar CausaRaiz",
        },
    )


@perfil_requerido(Perfil.RESPONSAVEL_SISTEMA)
@require_POST
def validar_solucao(request, pk):
    try:
        services.validar_solucao(
            usuario=request.user, problema_id=pk, decisao=request.POST.get("decisao")
        )
    except Problema.DoesNotExist as erro:
        raise Http404("Problema não encontrado.") from erro
    except ValidationError as erro:
        messages.error(request, " ".join(erro.messages))
    else:
        messages.success(request, "Decisão registrada.")
    return redirect("problemas:detalhe", pk=pk)
