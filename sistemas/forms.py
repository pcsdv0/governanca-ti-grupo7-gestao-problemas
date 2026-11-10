from django import forms

from .models import Sistema


class SistemaForm(forms.ModelForm):
    class Meta:
        model = Sistema
        fields = ["nome", "descricao", "responsavel"]
        help_texts = {
            "responsavel": "Selecione um usuário com o perfil Responsável pelo sistema.",
        }
        error_messages = {
            "responsavel": {
                "invalid_choice": "Selecione um usuário com o perfil Responsável pelo sistema.",
            },
        }
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "responsavel": forms.Select(attrs={"class": "form-select"}),
        }
