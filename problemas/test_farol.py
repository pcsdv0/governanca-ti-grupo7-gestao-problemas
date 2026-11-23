"""Testes do farol (verde, amarelo, vermelho) e da trilha de etapas do Problema."""

from datetime import date, timedelta
from types import SimpleNamespace

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from acoes.constantes import StatusAcaoCorretiva
from contas.models import Perfil, Usuario
from incidentes.constantes import ImpactoIncidente
from incidentes.models import Incidente
from sistemas.models import Sistema

from . import farol
from .constantes import PrioridadeProblema, StatusProblema
from .services import abrir_problema


class RegrasDoFarolTests(TestCase):
    def test_status_do_problema(self):
        esperado = {
            StatusProblema.REGISTRADO: farol.VERMELHO,
            StatusProblema.EM_INVESTIGACAO: farol.VERMELHO,
            StatusProblema.ERRO_CONHECIDO: farol.AMARELO,
            StatusProblema.EM_CORRECAO: farol.AMARELO,
            StatusProblema.RESOLVIDO: farol.VERDE,
            StatusProblema.ENCERRADO: farol.VERDE,
        }
        self.assertEqual(set(esperado), set(StatusProblema.values), "todo status precisa de cor")
        for status, cor in esperado.items():
            resultado = farol.farol_status(status)
            self.assertEqual(resultado.cor, cor, status)
            self.assertEqual(resultado.texto, StatusProblema(status).label)

    def test_impacto_e_prioridade(self):
        self.assertEqual(farol.farol_impacto(ImpactoIncidente.ALTO).cor, farol.VERMELHO)
        self.assertEqual(farol.farol_impacto(ImpactoIncidente.MEDIO).cor, farol.AMARELO)
        self.assertEqual(farol.farol_impacto(ImpactoIncidente.BAIXO).cor, farol.VERDE)
        self.assertEqual(farol.farol_prioridade(PrioridadeProblema.ALTA).cor, farol.VERMELHO)
        self.assertEqual(farol.farol_prioridade(PrioridadeProblema.MEDIA).cor, farol.AMARELO)
        self.assertEqual(farol.farol_prioridade(PrioridadeProblema.BAIXA).cor, farol.VERDE)
        self.assertEqual(farol.farol_prioridade("").cor, farol.SEM_DADOS)

    def test_prazo_da_acao(self):
        hoje = date(2026, 11, 22)

        def acao(status, dias):
            return SimpleNamespace(status=status, prazo=hoje + timedelta(days=dias))

        aberta = StatusAcaoCorretiva.ABERTA
        self.assertEqual(farol.farol_prazo_acao(acao(aberta, -1), hoje).cor, farol.VERMELHO)
        self.assertEqual(farol.farol_prazo_acao(acao(aberta, 0), hoje).texto, "Vence hoje")
        self.assertEqual(farol.farol_prazo_acao(acao(aberta, 2), hoje).cor, farol.AMARELO)
        self.assertEqual(farol.farol_prazo_acao(acao(aberta, 3), hoje).cor, farol.VERDE)
        concluida_atrasada = acao(StatusAcaoCorretiva.CONCLUIDA, -5)
        self.assertEqual(farol.farol_prazo_acao(concluida_atrasada, hoje).cor, farol.VERDE)

    def test_metas_dos_indicadores(self):
        self.assertEqual(farol.farol_tempo_medio(None).cor, farol.SEM_DADOS)
        self.assertEqual(farol.farol_tempo_medio(72).cor, farol.VERDE)
        self.assertEqual(farol.farol_tempo_medio(72.1).cor, farol.AMARELO)
        self.assertEqual(farol.farol_tempo_medio(168).cor, farol.AMARELO)
        self.assertEqual(farol.farol_tempo_medio(168.1).cor, farol.VERMELHO)
        self.assertEqual(farol.farol_acoes_no_prazo(None).cor, farol.SEM_DADOS)
        self.assertEqual(farol.farol_acoes_no_prazo(80).cor, farol.VERDE)
        self.assertEqual(farol.farol_acoes_no_prazo(79.9).cor, farol.AMARELO)
        self.assertEqual(farol.farol_acoes_no_prazo(50).cor, farol.AMARELO)
        self.assertEqual(farol.farol_acoes_no_prazo(49.9).cor, farol.VERMELHO)
        self.assertEqual(farol.farol_reincidencia(0).cor, farol.VERDE)
        self.assertEqual(farol.farol_reincidencia(1).cor, farol.VERMELHO)

    def test_problemas_abertos_e_sistema(self):
        self.assertEqual(farol.farol_problemas_abertos({}).cor, farol.VERDE)
        self.assertEqual(
            farol.farol_problemas_abertos({StatusProblema.ENCERRADO: 2}).cor, farol.VERDE
        )
        self.assertEqual(
            farol.farol_problemas_abertos({StatusProblema.EM_CORRECAO: 1}).cor, farol.AMARELO
        )
        self.assertEqual(
            farol.farol_problemas_abertos(
                {StatusProblema.EM_CORRECAO: 1, StatusProblema.REGISTRADO: 1}
            ).cor,
            farol.VERMELHO,
        )
        self.assertEqual(farol.farol_sistema(True, 0).cor, farol.VERMELHO)
        self.assertEqual(farol.farol_sistema(False, 1).cor, farol.AMARELO)
        self.assertEqual(farol.farol_sistema(False, 0).cor, farol.VERDE)


class FarolNasTelasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.suporte = Usuario.objects.create_user("sup", password="x", perfil=Perfil.SUPORTE)
        cls.gestor = Usuario.objects.create_user("ges", password="x", perfil=Perfil.GESTOR_TI)
        cls.responsavel = Usuario.objects.create_user(
            "resp", password="x", perfil=Perfil.RESPONSAVEL_SISTEMA
        )
        cls.sistema = Sistema.objects.create(nome="Matrícula", responsavel=cls.responsavel)
        cls.incidentes = [
            Incidente.objects.create(
                titulo=f"Queda {i}",
                descricao="Fora do ar",
                data_ocorrencia=timezone.now(),
                impacto=ImpactoIncidente.ALTO,
                sistema=cls.sistema,
                registrado_por=cls.suporte,
            )
            for i in range(3)
        ]
        cls.problema = abrir_problema(
            usuario=cls.suporte,
            titulo="Queda recorrente",
            descricao="Causa a investigar",
            incidentes_ids=[i.pk for i in cls.incidentes],
        )

    def test_detalhe_mostra_farol_e_trilha(self):
        self.client.force_login(self.suporte)
        resposta = self.client.get(reverse("problemas:detalhe", args=[self.problema.pk]))
        self.assertContains(resposta, 'data-farol="vermelho"')
        self.assertContains(resposta, 'class="trilha-status"')
        self.assertContains(resposta, 'aria-current="step"', count=1)
        self.assertContains(resposta, "Causa ainda desconhecida")

    def test_listas_mostram_farol_e_explicacao(self):
        self.client.force_login(self.suporte)
        incidentes = self.client.get(reverse("incidentes:listar"))
        self.assertContains(incidentes, "Incidente = o que aconteceu")
        self.assertContains(incidentes, "Problema (causa)")
        self.assertContains(incidentes, 'data-farol="vermelho"')
        problemas = self.client.get(reverse("problemas:listar"))
        self.assertContains(problemas, "Problema = por que acontece")
        self.assertContains(problemas, "Como ler as cores")

    def test_dashboard_mostra_farol_dos_indicadores(self):
        self.client.force_login(self.gestor)
        resposta = self.client.get(reverse("dashboard:painel"))
        self.assertEqual(resposta.context["farol_abertos"].cor, farol.VERMELHO)
        self.assertEqual(resposta.context["farol_reincidencia"].cor, farol.VERDE)
        self.assertContains(resposta, "card-farol-vermelho")
        self.assertContains(resposta, "Recorrência")
