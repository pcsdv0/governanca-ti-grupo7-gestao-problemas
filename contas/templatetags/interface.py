"""Filtros de interface compartilhados pelos templates (F3).

- ``codigo``: identificador exibido nas telas, como nos protótipos (INC-001, PRB-001).
- ``cor``: classe de cor do Bootstrap para status, prioridade e impacto.
- ``campo``: aplica a classe do Bootstrap ao widget sem alterar os formulários do backend.
"""

from django import forms, template

register = template.Library()

PREFIXOS = {"incidente": "INC", "problema": "PRB", "acaocorretiva": "AC"}

CORES = {
    # Status do Problema (docs/convencoes.md)
    "REGISTRADO": "secondary",
    "EM_INVESTIGACAO": "primary",
    "ERRO_CONHECIDO": "info",
    "EM_CORRECAO": "warning",
    "RESOLVIDO": "success",
    "ENCERRADO": "dark",
    # Status da AçãoCorretiva
    "ABERTA": "secondary",
    "EM_ANDAMENTO": "warning",
    "CONCLUIDA": "success",
    # Impacto e prioridade
    "ALTO": "danger",
    "ALTA": "danger",
    "MEDIO": "warning",
    "MEDIA": "warning",
    "BAIXO": "secondary",
    "BAIXA": "secondary",
}


@register.filter
def codigo(objeto):
    if not getattr(objeto, "pk", None):
        return ""
    prefixo = PREFIXOS.get(objeto._meta.model_name, objeto._meta.model_name[:3].upper())
    return f"{prefixo}-{objeto.pk:03d}"


@register.filter
def cor(valor):
    return CORES.get(valor, "secondary")


@register.filter
def campo(bound_field):
    """Renderiza o campo com a classe do Bootstrap adequada ao widget."""
    widget = bound_field.field.widget
    if isinstance(widget, forms.CheckboxSelectMultiple | forms.CheckboxInput):
        return bound_field
    classe = (
        "form-select" if isinstance(widget, forms.Select | forms.SelectMultiple) else "form-control"
    )
    atual = widget.attrs.get("class", "")
    if classe not in atual:
        return bound_field.as_widget(attrs={"class": f"{atual} {classe}".strip()})
    return bound_field


@register.filter
def tem_perfil(usuario, perfis):
    """Uso: {% if user|tem_perfil:"SUPORTE,GESTOR_TI" %}. Superusuário sempre passa."""
    from contas.permissoes import usuario_tem_perfil

    return usuario.is_authenticated and usuario_tem_perfil(usuario, perfis.split(","))


@register.filter
def proximo_status(objeto):
    """Próximo status na sequência sem saltos (Problema ou AçãoCorretiva), ou None."""
    from acoes.constantes import StatusAcaoCorretiva
    from problemas.constantes import StatusProblema

    choices = StatusProblema if objeto._meta.model_name == "problema" else StatusAcaoCorretiva
    valores = list(choices.values)
    indice = valores.index(objeto.status)
    if indice + 1 >= len(valores):
        return None
    proximo = valores[indice + 1]
    return {"valor": proximo, "rotulo": choices(proximo).label}


@register.filter
def etapas(problema):
    """Etapas do ciclo de status para a barra de progresso do detalhe do Problema."""
    from problemas.constantes import StatusProblema

    valores = list(StatusProblema.values)
    atual = valores.index(problema.status)
    return [
        {"rotulo": StatusProblema(v).label, "feito": i < atual, "atual": i == atual}
        for i, v in enumerate(valores)
    ]
