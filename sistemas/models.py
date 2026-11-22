from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from contas.models import Perfil


class Sistema(models.Model):
    nome = models.CharField("nome", max_length=200)
    descricao = models.TextField("descrição")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={"perfil": Perfil.RESPONSAVEL_SISTEMA},
        related_name="sistemas_responsaveis",
        verbose_name="Responsável pelo sistema",
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "sistema"
        verbose_name_plural = "sistemas"
        ordering = ["nome", "pk"]

    def __str__(self):
        return self.nome
