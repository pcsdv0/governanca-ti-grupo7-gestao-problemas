from django.db import transaction

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
