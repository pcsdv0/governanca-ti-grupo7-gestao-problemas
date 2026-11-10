from django.db import models
from simple_history.models import HistoricalRecords


class ErroConhecido(models.Model):
    sintoma = models.TextField("sintoma")
    causa = models.TextField("causa")
    solucao_contorno = models.TextField("solução de contorno")
    problema = models.OneToOneField(
        "problemas.Problema",
        on_delete=models.PROTECT,
        related_name="erro_conhecido",
        editable=False,
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "erro conhecido"
        verbose_name_plural = "erros conhecidos"
        ordering = ["-pk"]

    def __str__(self):
        return f"Erro conhecido do Problema {self.problema_id}"
