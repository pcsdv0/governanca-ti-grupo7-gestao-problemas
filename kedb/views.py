from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from contas.models import Perfil
from contas.permissoes import perfil_requerido
from problemas.forms import adicionar_erros
from problemas.models import Problema

from .forms import ErroConhecidoForm
from .models import ErroConhecido
from .services import registrar_erro_conhecido


@perfil_requerido(Perfil.DESENVOLVEDOR)
@require_http_methods(["GET", "POST"])
def registrar(request, problema_pk):
    problema = get_object_or_404(Problema, pk=problema_pk)
    erro = ErroConhecido.objects.filter(problema=problema).first()
    initial = (
        {
            "sintoma": erro.sintoma,
            "causa": erro.causa,
            "solucao_contorno": erro.solucao_contorno,
        }
        if erro
        else None
    )
    form = ErroConhecidoForm(
        request.POST if request.method == "POST" else None,
        initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        try:
            registrar_erro_conhecido(
                usuario=request.user,
                problema_id=problema.pk,
                **form.cleaned_data,
            )
        except Problema.DoesNotExist as exc:
            raise Http404("Problema não encontrado.") from exc
        except ValidationError as exc:
            adicionar_erros(form, exc)
        else:
            messages.success(request, "ErroConhecido salvo com sucesso.")
            return redirect("problemas:detalhe", pk=problema.pk)
    return render(
        request,
        "kedb/form.html",
        {
            "form": form,
            "problema": problema,
            "erro_conhecido": erro,
            "titulo": "Registrar ErroConhecido",
        },
    )
