from django import forms
from django.db.models import Q

from contas.models import Perfil, Usuario
from incidentes.models import Incidente

from .constantes import PrioridadeProblema, StatusProblema


class AbrirProblemaForm(forms.Form):
    titulo = forms.CharField(label="Título", max_length=200)
    descricao = forms.CharField(label="Descrição", widget=forms.Textarea)
    incidentes = forms.ModelMultipleChoiceField(
        label="Incidentes",
        queryset=Incidente.objects.filter(problema__isnull=True),
        help_text="Selecione um ou mais Incidentes do mesmo Sistema.",
    )


class VincularIncidentesForm(forms.Form):
    incidentes = forms.ModelMultipleChoiceField(
        label="Incidentes",
        queryset=Incidente.objects.none(),
    )

    def __init__(self, *args, problema, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["incidentes"].queryset = Incidente.objects.filter(
            Q(problema__isnull=True) | Q(problema=problema),
            sistema_id=problema.sistema_id,
        )


class AtribuirProblemaForm(forms.Form):
    responsavel = forms.ModelChoiceField(
        label="Responsável pelo Problema",
        queryset=Usuario.objects.filter(perfil=Perfil.DESENVOLVEDOR),
    )
    prioridade = forms.ChoiceField(
        label="Prioridade",
        choices=[("", "Selecione")] + PrioridadeProblema.choices,
    )


class AlterarStatusForm(forms.Form):
    status = forms.ChoiceField(label="Próximo status", choices=StatusProblema.choices)

    def __init__(self, *args, problema, **kwargs):
        super().__init__(*args, **kwargs)
        sequencia = StatusProblema.values
        indice = sequencia.index(problema.status)
        proximo = sequencia[indice + 1 : indice + 2]
        self.fields["status"].choices = [
            (valor, rotulo) for valor, rotulo in StatusProblema.choices if valor in proximo
        ]


class CausaRaizForm(forms.Form):
    descricao = forms.CharField(label="Descrição da causa raiz", widget=forms.Textarea)
    analise_5_porques = forms.CharField(
        label="Análise dos 5 Porquês",
        widget=forms.Textarea,
        help_text="Registre as perguntas e respostas que fundamentam a causa identificada.",
    )


def adicionar_erros(form, erro):
    """Expõe erros do serviço sem perder a associação aos campos do formulário."""
    if hasattr(erro, "message_dict"):
        for campo, mensagens in erro.message_dict.items():
            form.add_error(campo if campo in form.fields else None, mensagens)
    else:
        form.add_error(None, erro)
