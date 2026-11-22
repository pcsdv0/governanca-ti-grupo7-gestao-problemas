"""Formulários de Usuários (RF02): cadastro, edição e atribuição de perfil pelo Gestor de TI."""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


class UsuarioCriarForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "username", "email", "perfil"]
        labels = {"username": "Login"}


class UsuarioEditarForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "username", "email", "perfil", "is_active"]
        labels = {"username": "Login", "is_active": "Ativo"}
        help_texts = {
            "username": "",
            "is_active": "Desmarque para bloquear o acesso sem excluir o usuário.",
        }
