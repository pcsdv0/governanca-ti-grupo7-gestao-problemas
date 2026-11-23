"""Operações de negócio de Problemas. Use estes serviços também em scripts."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count

from acoes.constantes import StatusAcaoCorretiva
from acoes.models import AcaoCorretiva
from contas.models import Perfil, Usuario
from contas.permissoes import usuario_tem_perfil
from incidentes.models import Incidente
from sistemas.models import Sistema

from .constantes import StatusProblema
from .models import CausaRaiz, Problema


def exigir_perfil(usuario, *perfis):
    if (
        not usuario.is_authenticated
        or not usuario.is_active
        or not usuario_tem_perfil(usuario, perfis)
    ):
        raise PermissionDenied("Seu perfil não pode realizar esta operação.")


def problemas_visiveis(usuario):
    exigir_perfil(usuario, *Perfil.values)
    problemas = Problema.objects.select_related("sistema", "responsavel").annotate(
        quantidade_incidentes=Count("incidentes")
    )
    if not usuario.is_superuser and usuario.perfil == Perfil.RESPONSAVEL_SISTEMA:
        problemas = problemas.filter(sistema__responsavel=usuario)
    return problemas


def _selecionar_incidentes(incidentes_ids):
    try:
        ids = {int(pk) for pk in incidentes_ids}
    except (TypeError, ValueError) as erro:
        raise ValidationError("Selecione incidentes válidos.") from erro
    if not ids:
        raise ValidationError("Selecione pelo menos um Incidente.")
    incidentes = list(Incidente.objects.select_for_update().filter(pk__in=ids).order_by("pk"))
    if len(incidentes) != len(ids):
        raise ValidationError("Um dos chamados (Incidentes) selecionados não existe mais.")
    return incidentes


def _validar_vinculo(incidentes, sistema_id, problema_id=None):
    for incidente in incidentes:
        if incidente.sistema_id != sistema_id:
            raise ValidationError(
                "Todos os chamados (Incidentes) devem pertencer ao mesmo Sistema do Problema."
            )
        if incidente.problema_id and incidente.problema_id != problema_id:
            raise ValidationError(
                "Um dos chamados (Incidentes) já está vinculado a outro Problema."
            )


def _salvar(objeto, usuario):
    objeto.full_clean()
    objeto._history_user = usuario
    objeto.save()


def _vincular(problema, incidentes, usuario):
    for incidente in incidentes:
        if incidente.problema_id != problema.pk:
            incidente.problema = problema
            _salvar(incidente, usuario)


@transaction.atomic
def abrir_problema(*, usuario, titulo, descricao, incidentes_ids):
    exigir_perfil(usuario, Perfil.SUPORTE)
    incidentes = _selecionar_incidentes(incidentes_ids)
    sistema_id = incidentes[0].sistema_id
    _validar_vinculo(incidentes, sistema_id)
    problema = Problema(
        titulo=titulo.strip(),
        descricao=descricao.strip(),
        sistema_id=sistema_id,
    )
    _salvar(problema, usuario)
    _vincular(problema, incidentes, usuario)
    return problema


@transaction.atomic
def vincular_incidentes(*, usuario, problema_id, incidentes_ids):
    exigir_perfil(usuario, Perfil.SUPORTE)
    problema = Problema.objects.select_for_update().get(pk=problema_id)
    incidentes = _selecionar_incidentes(incidentes_ids)
    _validar_vinculo(incidentes, problema.sistema_id, problema.pk)
    _vincular(problema, incidentes, usuario)
    return problema


@transaction.atomic
def atribuir_responsavel_prioridade(*, usuario, problema_id, responsavel_id, prioridade):
    exigir_perfil(usuario, Perfil.GESTOR_TI)
    problema = Problema.objects.select_for_update().get(pk=problema_id)
    responsavel = Usuario.objects.filter(pk=responsavel_id, perfil=Perfil.DESENVOLVEDOR).first()
    if responsavel is None:
        raise ValidationError({"responsavel": "Selecione um usuário com perfil Desenvolvedor."})
    if not prioridade:
        raise ValidationError({"prioridade": "Selecione a prioridade."})
    problema.responsavel = responsavel
    problema.prioridade = prioridade
    _salvar(problema, usuario)
    return problema


def _exigir_acoes_concluidas(problema):
    acoes = AcaoCorretiva.objects.filter(problema=problema)
    if not acoes.exists():
        raise ValidationError(
            "O encerramento exige ao menos uma AçãoCorretiva concluída.", code="sem_acoes"
        )
    if acoes.exclude(status=StatusAcaoCorretiva.CONCLUIDA).exists():
        raise ValidationError(
            "Conclua todas as Ações Corretivas antes de encerrar o Problema.",
            code="acoes_pendentes",
        )


@transaction.atomic
def validar_solucao(*, usuario, problema_id, decisao):
    exigir_perfil(usuario, Perfil.RESPONSAVEL_SISTEMA)
    problema = Problema.objects.select_for_update().get(pk=problema_id)
    sistema = Sistema.objects.select_for_update().get(pk=problema.sistema_id)
    if not usuario.is_superuser and sistema.responsavel_id != usuario.pk:
        raise PermissionDenied("A validação cabe ao responsável pelo sistema afetado.")
    if problema.status != StatusProblema.RESOLVIDO or decisao not in ("validar", "rejeitar"):
        raise ValidationError("Selecione uma decisão válida para um problema resolvido.")
    _exigir_acoes_concluidas(problema)
    if decisao == "validar":
        if problema.validado_por_id == usuario.pk:
            return problema
        problema.validado_por = usuario
        problema._change_reason = "Solução validada"
    else:
        problema.status = StatusProblema.EM_INVESTIGACAO
        problema.validado_por = None
        problema._change_reason = "Solução rejeitada"
    problema._history_user = usuario
    problema.save(update_fields=["validado_por", "status"])
    return problema


@transaction.atomic
def alterar_status(*, usuario, problema_id, status):
    exigir_perfil(usuario, Perfil.DESENVOLVEDOR, Perfil.GESTOR_TI)
    problema = Problema.objects.select_for_update().get(pk=problema_id)
    sequencia = StatusProblema.values
    indice = sequencia.index(problema.status)
    if indice == len(sequencia) - 1 or status != sequencia[indice + 1]:
        raise ValidationError(
            "Avance somente para o próximo status; saltos e reabertura não são permitidos."
        )
    if status == StatusProblema.ENCERRADO:
        exigir_perfil(usuario, Perfil.GESTOR_TI)
        _exigir_acoes_concluidas(problema)
        sistema = Sistema.objects.select_for_update().get(pk=problema.sistema_id)
        if not problema.validado_por_id or (
            problema.validado_por_id != sistema.responsavel_id
            and not problema.validado_por.is_superuser
        ):
            raise ValidationError(
                "A solução aguarda validação do responsável pelo sistema.",
                code="validacao_pendente",
            )
    # Validações de atribuição pertencem ao RF11. Uma mudança posterior do perfil
    # do responsável não impede o registro da evolução técnica.
    problema.status = status
    problema._history_user = usuario
    problema.save(update_fields=["status"])
    return problema


@transaction.atomic
def registrar_causa_raiz(*, usuario, problema_id, descricao, analise_5_porques):
    exigir_perfil(usuario, Perfil.DESENVOLVEDOR)
    problema = Problema.objects.select_for_update().get(pk=problema_id)
    causa = CausaRaiz.objects.filter(problema=problema).first()
    if causa is None:
        causa = CausaRaiz(problema=problema)
    causa.descricao = descricao.strip()
    causa.analise_5_porques = analise_5_porques.strip()
    _salvar(causa, usuario)
    return causa
