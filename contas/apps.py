# Função 1 (F1): autenticação, perfis e controle de acesso.
from django.apps import AppConfig


class ContasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "contas"
    verbose_name = "Contas e perfis"
