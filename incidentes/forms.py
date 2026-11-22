from django import forms

from sistemas.models import Sistema

from .models import Incidente


class IncidenteForm(forms.ModelForm):
    class Meta:
        model = Incidente
        fields = ["titulo", "descricao", "data_ocorrencia", "impacto", "sistema"]
        help_texts = {
            "data_ocorrencia": "Informe a data e hora local (America/Recife).",
            "impacto": (
                "Baixo: efeito limitado, serviço principal disponível. "
                "Médio: degradação relevante ou indisponibilidade parcial. "
                "Alto: serviço essencial indisponível ou operação amplamente afetada."
            ),
        }
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "data_ocorrencia": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M:%S",
                attrs={"type": "datetime-local", "step": "1", "class": "form-control"},
            ),
            "impacto": forms.Select(attrs={"class": "form-select"}),
            "sistema": forms.Select(attrs={"class": "form-select"}),
        }


class FiltroIncidenteForm(forms.Form):
    vinculo_problema = forms.ChoiceField(
        label="Vínculo com Problema",
        required=False,
        choices=[("", "Todos"), ("com", "Com vínculo"), ("sem", "Sem vínculo")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    sistema = forms.ModelChoiceField(
        label="Sistema",
        queryset=Sistema.objects.all(),
        required=False,
        empty_label="Todos os sistemas",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    data_inicio = forms.DateField(
        label="De",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
    )
    data_fim = forms.DateField(
        label="Até",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
    )

    def __init__(self, *args, sistemas, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sistema"].queryset = sistemas

    def clean(self):
        dados = super().clean()
        inicio = dados.get("data_inicio")
        fim = dados.get("data_fim")
        if inicio and fim and inicio > fim:
            raise forms.ValidationError("A data inicial deve ser anterior ou igual à data final.")
        return dados
