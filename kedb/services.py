from django.db import transaction
from django.db.models import Q

from contas.models import Perfil
from problemas.models import Problema
from problemas.services import exigir_perfil

from .models import ErroConhecido


@transaction.atomic
def registrar_erro_conhecido(*, usuario, problema_id, sintoma, causa, solucao_contorno):
    exigir_perfil(usuario, Perfil.DESENVOLVEDOR)
    problema = Problema.objects.select_for_update().get(pk=problema_id)
    erro = ErroConhecido.objects.filter(problema=problema).first()
    if erro is None:
        erro = ErroConhecido(problema=problema)
    erro.sintoma = sintoma.strip()
    erro.causa = causa.strip()
    erro.solucao_contorno = solucao_contorno.strip()
    erro.full_clean()
    erro._history_user = usuario
    erro.save()
    return erro


def pesquisar_erros(*, usuario, termo=""):
    exigir_perfil(usuario, Perfil.SUPORTE, Perfil.DESENVOLVEDOR)
    erros = ErroConhecido.objects.select_related("problema__sistema")
    for palavra in termo.split():
        erros = erros.filter(
            Q(sintoma__icontains=palavra)
            | Q(causa__icontains=palavra)
            | Q(solucao_contorno__icontains=palavra)
        )
    return erros
