from django.dispatch import receiver
from simple_history.signals import post_create_historical_record

from .models import HistoricoStatus, Problema


@receiver(
    post_create_historical_record,
    sender=Problema.history.model,
    dispatch_uid="problemas.registrar_historico_status",
)
def registrar_historico_status(sender, history_instance, using, **kwargs):
    """Deriva a linha do tempo do mesmo registro que identifica o autor da auditoria."""
    if history_instance.history_type == "-":
        return
    anterior = history_instance.prev_record
    status_anterior = anterior.status if anterior else ""
    if status_anterior == history_instance.status:
        return
    evento = HistoricoStatus(
        problema_id=history_instance.id,
        status_anterior=status_anterior,
        status_novo=history_instance.status,
        data_alteracao=history_instance.history_date,
        usuario_id=history_instance.history_user_id,
    )
    evento._history_user = history_instance.history_user
    evento.save(using=using)
