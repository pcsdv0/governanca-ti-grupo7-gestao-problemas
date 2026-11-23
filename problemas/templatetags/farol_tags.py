"""Tags de template do farol (verde, amarelo, vermelho) e da trilha de etapas do Problema.

Uso nos templates:
    {% load farol_tags %}
    {% farol_selo problema.status|farol_status %}
    {% farol_selo incidente.impacto|farol_impacto %}
    {% farol_selo acao|farol_prazo %}
    {% trilha_status problema %}
"""

from django import template

from problemas import farol
from problemas.constantes import StatusProblema

register = template.Library()


@register.filter
def farol_status(status):
    return farol.farol_status(status)


@register.filter
def farol_impacto(impacto):
    return farol.farol_impacto(impacto)


@register.filter
def farol_prioridade(prioridade):
    return farol.farol_prioridade(prioridade)


@register.filter
def farol_prazo(acao):
    return farol.farol_prazo_acao(acao)


@register.inclusion_tag("farol/selo.html")
def farol_selo(objeto_farol, tamanho=""):
    """Selo com cor, ícone e texto; o significado aparece ao passar o mouse."""
    return {"farol": objeto_farol, "tamanho": tamanho}


@register.inclusion_tag("farol/trilha.html")
def trilha_status(problema):
    """Etapas do ciclo de vida do Problema, com a etapa atual destacada pela cor do farol."""
    sequencia = StatusProblema.values
    atual = sequencia.index(problema.status)
    etapas = []
    for indice, (valor, rotulo) in enumerate(StatusProblema.choices):
        if indice < atual:
            situacao = "concluida"
        elif indice == atual:
            situacao = "atual"
        else:
            situacao = "futura"
        etapas.append(
            {
                "numero": indice + 1,
                "rotulo": rotulo,
                "situacao": situacao,
                "cor": farol.COR_STATUS[valor],
            }
        )
    return {"etapas": etapas, "farol": farol.farol_status(problema.status)}


@register.inclusion_tag("farol/legenda.html")
def farol_legenda(contexto="problema"):
    """Legenda curta de como ler as cores na tela."""
    return {"contexto": contexto}
