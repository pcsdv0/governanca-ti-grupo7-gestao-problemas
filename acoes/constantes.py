"""
Status da Ação corretiva.

Fonte da verdade: docs/convencoes.md. Não altere nomes sem atualizar o documento.
"""

from django.db import models


class StatusAcaoCorretiva(models.TextChoices):
    ABERTA = "ABERTA", "Aberta"
    EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
    CONCLUIDA = "CONCLUIDA", "Concluída"
