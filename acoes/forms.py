from django import forms

from contas.models import Perfil, Usuario

from .constantes import StatusAcaoCorretiva


class AcaoCorretivaForm(forms.Form):
    descricao = forms.CharField(label="Descrição", widget=forms.Textarea)
    prazo = forms.DateField(
        label="Prazo",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    responsavel = forms.ModelChoiceField(
        label="Responsável pela ação",
        queryset=Usuario.objects.filter(perfil=Perfil.DESENVOLVEDOR),
    )


class AlterarStatusAcaoForm(forms.Form):
    status = forms.ChoiceField(label="Próximo status", choices=StatusAcaoCorretiva.choices)

    def __init__(self, *args, acao, **kwargs):
        super().__init__(*args, **kwargs)
        sequencia = StatusAcaoCorretiva.values
        indice = sequencia.index(acao.status)
        proximo = sequencia[indice + 1 : indice + 2]
        self.fields["status"].choices = [
            (valor, rotulo) for valor, rotulo in StatusAcaoCorretiva.choices if valor in proximo
        ]
