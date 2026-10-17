"""
Status do Problema (ciclo de vida ITIL 4 - Gestão de Problemas).

Fonte da verdade: docs/convencoes.md. Não altere nomes sem atualizar o documento.
"""

from django.db import models


class StatusProblema(models.TextChoices):
    REGISTRADO = "REGISTRADO", "Registrado"
    EM_INVESTIGACAO = "EM_INVESTIGACAO", "Em investigação"
    ERRO_CONHECIDO = "ERRO_CONHECIDO", "Erro conhecido"
    EM_CORRECAO = "EM_CORRECAO", "Em correção"
    RESOLVIDO = "RESOLVIDO", "Resolvido"
    ENCERRADO = "ENCERRADO", "Encerrado"
