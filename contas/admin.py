from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin padrão de usuários do Django com o campo perfil acrescentado."""

    list_display = ("username", "first_name", "last_name", "email", "perfil", "is_active")
    list_filter = ("perfil", "is_active", "is_staff")
    fieldsets = (*UserAdmin.fieldsets, ("Perfil no sistema", {"fields": ("perfil",)}))
    add_fieldsets = (*UserAdmin.add_fieldsets, ("Perfil no sistema", {"fields": ("perfil",)}))
