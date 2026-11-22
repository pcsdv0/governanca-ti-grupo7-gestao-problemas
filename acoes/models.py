from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from contas.models import Perfil

from .constantes import StatusAcaoCorretiva


class AcaoCorretiva(models.Model):
    descricao = models.TextField("descrição")
    prazo = models.DateField("prazo")
    status = models.CharField(
        "status",
        max_length=20,
        choices=StatusAcaoCorretiva.choices,
        default=StatusAcaoCorretiva.ABERTA,
        editable=False,
    )
    problema = models.ForeignKey(
        "problemas.Problema",
        on_delete=models.PROTECT,
        related_name="acoes_corretivas",
        editable=False,
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="acoes_corretivas_responsaveis",
        limit_choices_to={"perfil": Perfil.DESENVOLVEDOR},
        verbose_name="responsável pela ação",
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "ação corretiva"
        verbose_name_plural = "ações corretivas"
        ordering = ["prazo", "pk"]

    def __str__(self):
        return f"Ação {self.pk} do Problema {self.problema_id}"
