from django import forms


class ErroConhecidoForm(forms.Form):
    sintoma = forms.CharField(label="Sintoma", widget=forms.Textarea)
    causa = forms.CharField(label="Causa", widget=forms.Textarea)
    solucao_contorno = forms.CharField(label="Solução de contorno", widget=forms.Textarea)
