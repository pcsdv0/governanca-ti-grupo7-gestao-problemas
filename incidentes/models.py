from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from .constantes import ImpactoIncidente


class Incidente(models.Model):
    titulo = models.CharField("título", max_length=200)
    descricao = models.TextField("descrição")
    data_ocorrencia = models.DateTimeField("data e hora da ocorrência")
    impacto = models.CharField("impacto", max_length=5, choices=ImpactoIncidente.choices)
    sistema = models.ForeignKey(
        "sistemas.Sistema",
        on_delete=models.PROTECT,
        related_name="incidentes",
        verbose_name="Sistema afetado",
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="incidentes_registrados",
        verbose_name="registrado por",
        editable=False,
    )
    problema = models.ForeignKey(
        "problemas.Problema",
        on_delete=models.PROTECT,
        related_name="incidentes",
        verbose_name="Problema",
        null=True,
        blank=True,
        editable=False,
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "incidente"
        verbose_name_plural = "incidentes"
        ordering = ["-data_ocorrencia", "-pk"]

    def __str__(self):
        return self.titulo

    def clean(self):
        super().clean()
        if self.problema_id and self.sistema_id != self.problema.sistema_id:
            raise ValidationError({"sistema": "O Sistema deve ser o mesmo do Problema vinculado."})
