from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from contas.models import Perfil

from .constantes import PrioridadeProblema, StatusProblema


class Problema(models.Model):
    titulo = models.CharField("título", max_length=200)
    descricao = models.TextField("descrição")
    status = models.CharField(
        "status",
        max_length=20,
        choices=StatusProblema.choices,
        default=StatusProblema.REGISTRADO,
        editable=False,
    )
    prioridade = models.CharField(
        "prioridade",
        max_length=5,
        choices=PrioridadeProblema.choices,
        blank=True,
    )
    sistema = models.ForeignKey(
        "sistemas.Sistema",
        on_delete=models.PROTECT,
        related_name="problemas",
        verbose_name="Sistema afetado",
        editable=False,
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="problemas_responsaveis",
        verbose_name="responsável pelo Problema",
        null=True,
        blank=True,
        limit_choices_to={"perfil": Perfil.DESENVOLVEDOR},
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
        editable=False,
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "problema"
        verbose_name_plural = "problemas"
        ordering = ["-pk"]

    def __str__(self):
        return self.titulo


class HistoricoStatus(models.Model):
    problema = models.ForeignKey(
        Problema,
        on_delete=models.PROTECT,
        related_name="historico_status",
    )
    status_anterior = models.CharField(
        max_length=20,
        choices=StatusProblema.choices,
        blank=True,
    )
    status_novo = models.CharField(max_length=20, choices=StatusProblema.choices)
    data_alteracao = models.DateTimeField()
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="alteracoes_status_problemas",
        null=True,
        blank=True,
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "histórico de status"
        verbose_name_plural = "históricos de status"
        ordering = ["data_alteracao", "pk"]

    def __str__(self):
        return f"{self.problema_id}: {self.get_status_novo_display()}"


class CausaRaiz(models.Model):
    descricao = models.TextField("descrição")
    analise_5_porques = models.TextField("análise dos 5 Porquês")
    problema = models.OneToOneField(
        Problema,
        on_delete=models.PROTECT,
        related_name="causa_raiz",
        editable=False,
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "causa raiz"
        verbose_name_plural = "causas raiz"
        ordering = ["-pk"]

    def __str__(self):
        return f"Causa raiz do Problema {self.problema_id}"
