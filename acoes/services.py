from django.core.exceptions import ValidationError
from django.db import transaction

from contas.models import Perfil
from problemas.constantes import StatusProblema
from problemas.models import Problema
from problemas.services import exigir_perfil

from .constantes import StatusAcaoCorretiva
from .models import AcaoCorretiva


def _exigir_problema_aberto(problema):
    if problema.status == StatusProblema.ENCERRADO:
        raise ValidationError(
            "Não é permitido criar ações ou alterar seu status em um Problema encerrado.",
            code="problema_encerrado",
        )


@transaction.atomic
def criar_acao(*, usuario, problema_id, descricao, prazo, responsavel_id):
    exigir_perfil(usuario, Perfil.DESENVOLVEDOR, Perfil.GESTOR_TI)
    # Todas as mutações de ações e o encerramento bloqueiam primeiro o Problema.
    problema = Problema.objects.select_for_update().get(pk=problema_id)
    _exigir_problema_aberto(problema)
    acao = AcaoCorretiva(
        problema=problema,
        descricao=descricao.strip(),
        prazo=prazo,
        responsavel_id=responsavel_id,
    )
    acao.full_clean()
    acao._history_user = usuario
    acao.save()
    if problema.validado_por_id:
        problema.validado_por = None
        problema._history_user = usuario
        problema._change_reason = "Nova ação requer outra validação"
        problema.save(update_fields=["validado_por"])
    return acao


@transaction.atomic
def alterar_status_acao(*, usuario, acao_id, status):
    exigir_perfil(usuario, Perfil.DESENVOLVEDOR)
    problema_id = AcaoCorretiva.objects.values_list("problema_id", flat=True).get(pk=acao_id)
    problema = Problema.objects.select_for_update().get(pk=problema_id)
    _exigir_problema_aberto(problema)
    acao = AcaoCorretiva.objects.select_for_update().get(pk=acao_id, problema_id=problema.pk)
    sequencia = StatusAcaoCorretiva.values
    indice = sequencia.index(acao.status)
    if indice == len(sequencia) - 1 or status != sequencia[indice + 1]:
        raise ValidationError(
            "Avance somente para o próximo status da ação; saltos e retornos não são permitidos."
        )
    acao.status = status
    acao._history_user = usuario
    acao.save(update_fields=["status"])
    return acao
