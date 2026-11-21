from collections import defaultdict
from datetime import timedelta

from django.db.models import Avg, Count, F, Max, Min, OuterRef, Q, Subquery
from django.db.models.functions import TruncDate
from django.utils import timezone

from acoes.constantes import StatusAcaoCorretiva
from acoes.models import AcaoCorretiva
from contas.models import Perfil
from incidentes.models import Incidente
from problemas.constantes import StatusProblema
from problemas.models import HistoricoStatus, Problema
from problemas.services import exigir_perfil
from sistemas.models import Sistema


def _recorrencias(agora):
    """Agrupa por título ou problema e conta cada incidente uma vez por sistema."""
    recentes = (
        Incidente.objects.filter(data_ocorrencia__range=(agora - timedelta(days=30), agora))
        .order_by("pk")
        .values_list("pk", "sistema_id", "titulo", "problema_id")
    )
    por_titulo = defaultdict(set)
    por_problema = defaultdict(set)
    for pk, sistema, titulo, problema in recentes.iterator():
        sintoma = " ".join(titulo.casefold().split())
        por_titulo[sistema, sintoma].add(pk)
        if problema is not None:
            por_problema[sistema, problema].add(pk)

    ocorrencias = defaultdict(set)
    alertas = []
    grupos_emitidos = set()
    for tipo, grupos in (("Problema", por_problema), ("Título", por_titulo)):
        for (sistema, chave), ids in grupos.items():
            membros = frozenset(ids)
            if len(ids) < 3 or membros in grupos_emitidos:
                continue
            grupos_emitidos.add(membros)
            ocorrencias[sistema].update(ids)
            alertas.append(
                {"sistema_id": sistema, "tipo": tipo, "chave": chave, "quantidade": len(ids)}
            )
    return alertas, ocorrencias


def _resolucao_e_reincidencia(agora):
    resolvidos = Problema.objects.filter(
        status__in=[StatusProblema.RESOLVIDO, StatusProblema.ENCERRADO]
    ).annotate(
        registro=Min(
            "historico_status__data_alteracao",
            filter=Q(historico_status__status_novo=StatusProblema.REGISTRADO),
        ),
        resolucao=Max(
            "historico_status__data_alteracao",
            filter=Q(historico_status__status_novo=StatusProblema.RESOLVIDO),
        ),
    )
    media = resolvidos.aggregate(tempo=Avg(F("resolucao") - F("registro")))["tempo"]
    ultima_resolucao = (
        HistoricoStatus.objects.filter(
            problema_id=OuterRef("problema_id"), status_novo=StatusProblema.RESOLVIDO
        )
        .order_by("-data_alteracao")
        .values("data_alteracao")[:1]
    )
    reincidentes = (
        Incidente.objects.filter(
            problema__status__in=[StatusProblema.RESOLVIDO, StatusProblema.ENCERRADO],
            data_ocorrencia__gt=Subquery(ultima_resolucao),
            data_ocorrencia__lte=agora,
        )
        .order_by()
        .values("problema_id")
        .distinct()
        .count()
    )
    horas = media.total_seconds() / 3600 if media is not None else None
    return horas, reincidentes


def _percentual_acoes_no_prazo():
    conclusao = AcaoCorretiva.history.filter(
        id=OuterRef("pk"), status=StatusAcaoCorretiva.CONCLUIDA
    ).order_by("history_date", "history_id")
    prazos = (
        AcaoCorretiva.objects.filter(status=StatusAcaoCorretiva.CONCLUIDA)
        .annotate(dia=TruncDate(Subquery(conclusao.values("history_date")[:1])))
        .aggregate(total=Count("dia"), no_prazo=Count("pk", filter=Q(dia__lte=F("prazo"))))
    )

    if not prazos["total"]:
        return None
    return 100 * prazos["no_prazo"] / prazos["total"]


def indicadores(*, usuario, agora=None):
    exigir_perfil(usuario, Perfil.GESTOR_TI)
    agora = agora or timezone.now()
    alertas, recorrentes = _recorrencias(agora)
    sistemas = list(
        Sistema.objects.annotate(
            total_incidentes=Count("incidentes", distinct=True),
            total_problemas=Count("problemas", distinct=True),
        )
    )
    nomes = {s.pk: s.nome for s in sistemas}
    for sistema in sistemas:
        sistema.incidentes_recorrentes = len(recorrentes.get(sistema.pk, ()))
    for alerta in alertas:
        alerta["sistema"] = nomes[alerta["sistema_id"]]

    problemas = Problema.objects.annotate(incidentes_vinculados=Count("incidentes"))
    por_status = dict(
        Problema.objects.order_by()
        .values("status")
        .annotate(n=Count("pk"))
        .values_list("status", "n")
    )
    por_status_incidente = dict(
        Incidente.objects.order_by()
        .values("problema__status")
        .annotate(n=Count("pk"))
        .values_list("problema__status", "n")
    )
    status = [
        {
            "nome": nome,
            "problemas": por_status.get(codigo, 0),
            "incidentes": por_status_incidente.get(codigo, 0),
        }
        for codigo, nome in StatusProblema.choices
    ]
    tempo_medio, reincidentes = _resolucao_e_reincidencia(agora)

    return {
        "por_sistema": sistemas,
        "por_status": status,
        "incidentes_sem_problema": por_status_incidente.get(None, 0),
        "por_problema": problemas,
        "alertas": alertas,
        "problemas_abertos": sum(por_status.values())
        - por_status.get(StatusProblema.RESOLVIDO, 0)
        - por_status.get(StatusProblema.ENCERRADO, 0),
        "tempo_medio_horas": tempo_medio,
        "percentual_acoes_no_prazo": _percentual_acoes_no_prazo(),
        "problemas_reincidentes": reincidentes,
    }
