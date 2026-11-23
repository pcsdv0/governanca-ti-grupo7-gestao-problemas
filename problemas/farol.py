"""Farol de governança: verde, amarelo e vermelho.

Fonte única das regras de cor do sistema (telas, dashboard e testes usam este módulo).
A cor sempre vem acompanhada de ícone e texto, para não depender só da cor (acessibilidade).

Leitura geral do farol:
- vermelho: exige ação agora (causa desconhecida, impacto alto, prazo vencido, meta não atingida);
- amarelo: em tratamento ou em atenção (causa conhecida, correção em andamento, prazo próximo);
- verde: sob controle (solução aplicada, prazo cumprido, meta atingida).
"""

from dataclasses import dataclass
from datetime import date

from acoes.constantes import StatusAcaoCorretiva
from incidentes.constantes import ImpactoIncidente

from .constantes import PrioridadeProblema, StatusProblema

VERDE = "verde"
AMARELO = "amarelo"
VERMELHO = "vermelho"
SEM_DADOS = "sem-dados"

ICONES = {
    VERDE: "bi-check-circle-fill",
    AMARELO: "bi-exclamation-triangle-fill",
    VERMELHO: "bi-exclamation-octagon-fill",
    SEM_DADOS: "bi-dash-circle",
}

# Prazo (em dias) a partir do qual uma ação ainda não concluída fica amarela.
DIAS_ALERTA_PRAZO = 2

# Metas dos indicadores do dashboard (definidas pela equipe; ver documentação, Seção 4.5.5).
META_TEMPO_VERDE_HORAS = 72  # até 3 dias
META_TEMPO_AMARELO_HORAS = 168  # até 7 dias
META_PRAZO_VERDE = 80.0  # % de ações concluídas no prazo
META_PRAZO_AMARELO = 50.0


@dataclass(frozen=True)
class Farol:
    cor: str
    texto: str
    significado: str

    @property
    def icone(self):
        return ICONES[self.cor]


# --------------------------------------------------------------------------- Problema
SIGNIFICADO_STATUS = {
    VERMELHO: "Causa ainda desconhecida: risco de novas ocorrências.",
    AMARELO: "Causa conhecida: há solução de contorno e a correção está em tratamento.",
    VERDE: "Solução definitiva aplicada.",
}

COR_STATUS = {
    StatusProblema.REGISTRADO: VERMELHO,
    StatusProblema.EM_INVESTIGACAO: VERMELHO,
    StatusProblema.ERRO_CONHECIDO: AMARELO,
    StatusProblema.EM_CORRECAO: AMARELO,
    StatusProblema.RESOLVIDO: VERDE,
    StatusProblema.ENCERRADO: VERDE,
}


def farol_status(status):
    """Farol do Problema pelo status do ciclo de vida."""
    cor = COR_STATUS[status]
    return Farol(cor, StatusProblema(status).label, SIGNIFICADO_STATUS[cor])


# --------------------------------------------------------------------------- impacto e prioridade
COR_NIVEL = {
    ImpactoIncidente.ALTO: VERMELHO,
    ImpactoIncidente.MEDIO: AMARELO,
    ImpactoIncidente.BAIXO: VERDE,
    PrioridadeProblema.ALTA: VERMELHO,
    PrioridadeProblema.MEDIA: AMARELO,
    PrioridadeProblema.BAIXA: VERDE,
}


def farol_impacto(impacto):
    cor = COR_NIVEL[impacto]
    return Farol(
        cor, ImpactoIncidente(impacto).label, f"Impacto {ImpactoIncidente(impacto).label.lower()}."
    )


def farol_prioridade(prioridade):
    if not prioridade:
        return Farol(SEM_DADOS, "Não definida", "Prioridade ainda não definida pelo Gestor de TI.")
    cor = COR_NIVEL[prioridade]
    rotulo = PrioridadeProblema(prioridade).label
    return Farol(cor, rotulo, f"Prioridade {rotulo.lower()}.")


# --------------------------------------------------------------------------- ação corretiva
def farol_prazo_acao(acao, hoje=None):
    """Farol do prazo da AçãoCorretiva: atrasada, vencendo ou no prazo."""
    hoje = hoje or date.today()
    if acao.status == StatusAcaoCorretiva.CONCLUIDA:
        return Farol(VERDE, "Concluída", "Ação concluída.")
    dias = (acao.prazo - hoje).days
    if dias < 0:
        return Farol(VERMELHO, "Atrasada", f"Prazo vencido há {-dias} dia(s).")
    if dias <= DIAS_ALERTA_PRAZO:
        texto = "Vence hoje" if dias == 0 else f"Vence em {dias} dia(s)"
        return Farol(AMARELO, texto, "Prazo próximo do vencimento.")
    return Farol(VERDE, "No prazo", f"Faltam {dias} dias para o prazo.")


# --------------------------------------------------------------------------- indicadores
def farol_problemas_abertos(contagem_por_status):
    """Vermelho se há Problema sem causa conhecida; amarelo se só há Problemas em tratamento."""
    sem_causa = sum(
        contagem_por_status.get(s, 0)
        for s in (StatusProblema.REGISTRADO, StatusProblema.EM_INVESTIGACAO)
    )
    em_tratamento = sum(
        contagem_por_status.get(s, 0)
        for s in (StatusProblema.ERRO_CONHECIDO, StatusProblema.EM_CORRECAO)
    )
    if sem_causa:
        return Farol(VERMELHO, "Exige ação", f"{sem_causa} Problema(s) ainda sem causa conhecida.")
    if em_tratamento:
        return Farol(AMARELO, "Em tratamento", "Todos os Problemas abertos já têm causa conhecida.")
    return Farol(VERDE, "Sob controle", "Nenhum Problema em aberto.")


def farol_tempo_medio(horas):
    if horas is None:
        return Farol(SEM_DADOS, "Sem dados", "Ainda não há Problemas resolvidos.")
    if horas <= META_TEMPO_VERDE_HORAS:
        return Farol(VERDE, "Dentro da meta", f"Meta: até {META_TEMPO_VERDE_HORAS} h.")
    if horas <= META_TEMPO_AMARELO_HORAS:
        return Farol(AMARELO, "Atenção", f"Acima de {META_TEMPO_VERDE_HORAS} h (meta).")
    return Farol(VERMELHO, "Fora da meta", f"Acima de {META_TEMPO_AMARELO_HORAS} h.")


def farol_acoes_no_prazo(percentual):
    if percentual is None:
        return Farol(SEM_DADOS, "Sem dados", "Ainda não há ações concluídas.")
    if percentual >= META_PRAZO_VERDE:
        return Farol(VERDE, "Dentro da meta", f"Meta: {META_PRAZO_VERDE:.0f}% ou mais.")
    if percentual >= META_PRAZO_AMARELO:
        return Farol(AMARELO, "Atenção", f"Abaixo de {META_PRAZO_VERDE:.0f}% (meta).")
    return Farol(VERMELHO, "Fora da meta", f"Abaixo de {META_PRAZO_AMARELO:.0f}%.")


def farol_reincidencia(quantidade):
    if quantidade:
        return Farol(VERMELHO, "Reincidência", "A correção não eliminou a causa: reavaliar.")
    return Farol(VERDE, "Sem reincidência", "Nenhum Incidente depois do encerramento.")


def farol_sistema(tem_alerta, problemas_abertos):
    """Situação do Sistema no dashboard."""
    if tem_alerta:
        return Farol(VERMELHO, "Recorrência", "Três ou mais Incidentes semelhantes em 30 dias.")
    if problemas_abertos:
        return Farol(AMARELO, "Em tratamento", "Há Problema em aberto neste Sistema.")
    return Farol(VERDE, "Estável", "Sem recorrência nem Problema em aberto.")
