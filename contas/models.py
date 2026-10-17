from django.contrib.auth.models import AbstractUser
from django.db import models


class Perfil(models.TextChoices):
    """Perfis de usuário. Fonte da verdade: docs/convencoes.md."""

    SUPORTE = "SUPORTE", "Suporte"
    DESENVOLVEDOR = "DESENVOLVEDOR", "Desenvolvedor"
    GESTOR_TI = "GESTOR_TI", "Gestor de TI"
    RESPONSAVEL_SISTEMA = "RESPONSAVEL_SISTEMA", "Responsável pelo sistema"


class Usuario(AbstractUser):
    """
    Usuário do sistema. Herda login, senha, nome e e-mail do Django e acrescenta
    o perfil, que define o que cada pessoa pode fazer (ver contas/permissoes.py).
    """

    # Padrão SUPORTE: o perfil com menos permissões (menor privilégio).
    perfil = models.CharField(
        "perfil",
        max_length=30,
        choices=Perfil.choices,
        default=Perfil.SUPORTE,
    )

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self):
        return self.get_full_name() or self.username
