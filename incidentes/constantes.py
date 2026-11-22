from django.db import models


class ImpactoIncidente(models.TextChoices):
    BAIXO = "BAIXO", "Baixo"
    MEDIO = "MEDIO", "Médio"
    ALTO = "ALTO", "Alto"
