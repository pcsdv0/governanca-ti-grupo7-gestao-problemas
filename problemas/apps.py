from django.apps import AppConfig


class ProblemasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "problemas"
    verbose_name = "Problemas"

    def ready(self):
        from . import signals  # noqa: F401
