from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from contas.models import Perfil
from contas.permissoes import usuario_tem_perfil

from .forms import SistemaForm
from .models import Sistema


@admin.register(Sistema)
class SistemaAdmin(SimpleHistoryAdmin):
    form = SistemaForm
    list_display = ("nome", "responsavel")
    list_select_related = ("responsavel",)
    search_fields = ("nome",)

    def has_module_permission(self, request):
        return usuario_tem_perfil(
            request.user, [Perfil.GESTOR_TI]
        ) and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return usuario_tem_perfil(request.user, [Perfil.GESTOR_TI]) and super().has_view_permission(
            request, obj
        )

    def has_add_permission(self, request):
        return usuario_tem_perfil(request.user, [Perfil.GESTOR_TI]) and super().has_add_permission(
            request
        )

    def has_change_permission(self, request, obj=None):
        return usuario_tem_perfil(
            request.user, [Perfil.GESTOR_TI]
        ) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False
